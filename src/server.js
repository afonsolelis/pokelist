import dotenv from 'dotenv'
import express from 'express'
import path from 'path'
import expressLayouts from 'express-ejs-layouts'
import methodOverride from 'method-override'
import { fileURLToPath } from 'url'
import { query } from './db.js'
import { normalizeCloudinary, thumbCloudinary } from './cloudinary.js'
import multer from 'multer'
import { uploadBuffer } from './cloudinaryClient.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
// Load env from repo root if available, then from cwd
dotenv.config({ path: path.resolve(__dirname, '../../.env') })
dotenv.config()

const app = express()
const port = process.env.PORT || 3000

app.set('views', path.join(__dirname, '../views'))
app.set('view engine', 'ejs')
app.use(expressLayouts)
app.set('layout', 'layout')

app.use(express.urlencoded({ extended: true }))
app.use(methodOverride('_method'))
app.use('/static', express.static(path.join(__dirname, '../public')))

app.locals.normalizeCloudinary = normalizeCloudinary
app.locals.thumbCloudinary = thumbCloudinary

// Upload setup (memory)
const upload = multer({ storage: multer.memoryStorage() })

// Auth helpers (cookie-based, simples)
const PASSWORD = process.env.password || ''
function parseCookies (cookieHeader = '') {
  return Object.fromEntries(
    cookieHeader.split(';').map(v => v.trim()).filter(Boolean).map(pair => {
      const idx = pair.indexOf('=')
      if (idx === -1) return [pair, '']
      const k = decodeURIComponent(pair.slice(0, idx))
      const v = decodeURIComponent(pair.slice(idx + 1))
      return [k, v]
    })
  )
}
function isAuthed (req) {
  const cookies = parseCookies(req.headers.cookie || '')
  return cookies.auth === '1'
}
function authMiddleware (req, res, next) {
  res.locals.authed = isAuthed(req)
  next()
}
function requireAuth (req, res, next) {
  if (isAuthed(req)) return next()
  // Redireciona para view-only quando possível
  if (req.path.startsWith('/list/') && /\/list\/(\d+)$/.test(req.path)) {
    const id = req.path.match(/\/list\/(\d+)$/)[1]
    return res.redirect(`/list/${id}/view`)
  }
  if (req.path.startsWith('/card/') && /\/card\/(\d+)$/.test(req.path)) {
    const id = req.path.match(/\/card\/(\d+)$/)[1]
    return res.redirect(`/card/${id}/view`)
  }
  return res.redirect('/login')
}

app.use(authMiddleware)

// Constants
const LANGUAGES = [
  'Português', 'Inglês', 'Japonês', 'Italiano', 'Espanhol',
  'Alemão', 'Francês', 'Chinês Simplificado', 'Chinês Tradicional', 'Coreano',
]
const CONDITIONS = ['GM', 'M', 'NM', 'SP', 'MP', 'HP', 'D']
const CARD_TYPES = [
  'Normal', 'Foil', 'Reverse Foil', 'Assinada', 'Promo', 'Textless', 'Alterada',
  'Pre Release', 'Edition One', 'Shadowless', 'Staff', 'Misprint', 'Shattered Holo',
  'Master Ball', 'Poke Ball',
]

// Home: listas
app.get('/', async (req, res, next) => {
  try {
    const { rows } = await query(
      `SELECT l.id, l.name, COUNT(c.id) as total
       FROM lists l
       LEFT JOIN cards c ON c.list_id = l.id
       GROUP BY l.id, l.name
       ORDER BY l.name ASC`
    )
    res.render('index', { title: 'Minhas Listas', lists: rows })
  } catch (e) { next(e) }
})

// Login simples
app.get('/login', (req, res) => {
  if (isAuthed(req)) return res.redirect('/')
  res.render('login', { title: 'Login', error: '' })
})
app.post('/login', (req, res) => {
  const { password } = req.body
  if (PASSWORD && password === PASSWORD) {
    res.setHeader('Set-Cookie', 'auth=1; HttpOnly; Path=/; SameSite=Lax; Max-Age=2592000') // 30 dias
    return res.redirect('back')
  }
  res.status(401)
  res.render('login', { title: 'Login', error: 'Senha inválida' })
})
app.post('/logout', (req, res) => {
  res.setHeader('Set-Cookie', 'auth=; HttpOnly; Path=/; SameSite=Lax; Max-Age=0')
  res.redirect('back')
})

// Criar nova lista
app.post('/lists', requireAuth, async (req, res, next) => {
  try {
    const name = (req.body.name || '').trim()
    if (name) await query('INSERT INTO lists (name) VALUES ($1)', [name])
    res.redirect('/')
  } catch (e) { next(e) }
})

// Detalhe da lista
app.get('/list/:id', requireAuth, async (req, res, next) => {
  try {
    const listId = parseInt(req.params.id, 10)
    const listRes = await query('SELECT id, name FROM lists WHERE id = $1', [listId])
    if (!listRes.rows.length) return res.status(404).send('Lista não encontrada')
    const list = listRes.rows[0]
    const cardsRes = await query(
      `SELECT id, name, photo_url, card_number, collection_total, language,
              card_order, grading_note, condition, owned, COALESCE(card_type,'Normal') AS card_type
         FROM cards WHERE list_id = $1 ORDER BY card_order ASC`,
      [listId]
    )
    res.render('list_detail', { title: list.name, list, cards: cardsRes.rows, LANGUAGES, CONDITIONS, CARD_TYPES })
  } catch (e) { next(e) }
})

// Visualização somente da coleção (read-only)
app.get('/list/:id/view', async (req, res, next) => {
  try {
    const listId = parseInt(req.params.id, 10)
    const listRes = await query('SELECT id, name FROM lists WHERE id = $1', [listId])
    if (!listRes.rows.length) return res.status(404).send('Lista não encontrada')
    const list = listRes.rows[0]
    const cardsRes = await query(
      `SELECT id, name, photo_url, card_number, collection_total, language,
              card_order, grading_note, condition, owned, COALESCE(card_type,'Normal') AS card_type
         FROM cards WHERE list_id = $1 ORDER BY card_order ASC`,
      [listId]
    )
    res.render('list_view', { title: list.name, list, cards: cardsRes.rows, LANGUAGES, CONDITIONS, CARD_TYPES })
  } catch (e) { next(e) }
})

// Detalhe do card
app.get('/card/:id', requireAuth, async (req, res, next) => {
  try {
    const cardId = parseInt(req.params.id, 10)
    const { rows } = await query(
      `SELECT c.id, c.name, c.photo_url, c.card_number, c.collection_total,
              c.language, c.card_order, c.grading_note, c.condition, c.owned,
              COALESCE(c.card_type,'Normal') as card_type,
              l.id as list_id, l.name as list_name
         FROM cards c JOIN lists l ON l.id = c.list_id
        WHERE c.id = $1`,
      [cardId]
    )
    if (!rows.length) return res.status(404).send('Card não encontrado')
    res.render('card_detail', { title: rows[0].name, card: rows[0], LANGUAGES, CONDITIONS, CARD_TYPES })
  } catch (e) { next(e) }
})

// Visualização somente do card (read-only)
app.get('/card/:id/view', async (req, res, next) => {
  try {
    const cardId = parseInt(req.params.id, 10)
    const { rows } = await query(
      `SELECT c.id, c.name, c.photo_url, c.card_number, c.collection_total,
              c.language, c.card_order, c.grading_note, c.condition, c.owned,
              COALESCE(c.card_type,'Normal') as card_type,
              l.id as list_id, l.name as list_name
         FROM cards c JOIN lists l ON l.id = c.list_id
        WHERE c.id = $1`,
      [cardId]
    )
    if (!rows.length) return res.status(404).send('Card não encontrado')
    res.render('card_view', { title: rows[0].name, card: rows[0] })
  } catch (e) { next(e) }
})

// Busca global por cards (independente da coleção)
app.get('/search', async (req, res, next) => {
  try {
    const { q = '', condition = '', language = '', card_type = '', owned = '', grading_min = '', grading_max = '' } = req.query
    const where = []
    const params = []

    if (q && String(q).trim()) {
      params.push(`%${String(q).trim()}%`)
      where.push(`c.name ILIKE $${params.length}`)
    }
    if (condition) {
      params.push(condition)
      where.push(`c.condition = $${params.length}`)
    }
    if (language) {
      params.push(language)
      where.push(`c.language = $${params.length}`)
    }
    if (card_type) {
      params.push(card_type)
      where.push(`COALESCE(c.card_type,'Normal') = $${params.length}`)
    }
    if (owned === 'true' || owned === 'false') {
      params.push(owned === 'true')
      where.push(`COALESCE(c.owned,false) = $${params.length}`)
    }
    if (grading_min !== '') {
      const v = parseInt(grading_min, 10)
      if (!Number.isNaN(v)) {
        params.push(v)
        where.push(`COALESCE(c.grading_note, 0) >= $${params.length}`)
      }
    }
    if (grading_max !== '') {
      const v = parseInt(grading_max, 10)
      if (!Number.isNaN(v)) {
        params.push(v)
        where.push(`COALESCE(c.grading_note, 0) <= $${params.length}`)
      }
    }

    const sql = `
      SELECT c.id, c.name, c.photo_url, c.card_number, c.collection_total,
             c.language, c.grading_note, c.condition, COALESCE(c.card_type,'Normal') as card_type,
             c.owned, l.id as list_id, l.name as list_name
        FROM cards c
        JOIN lists l ON l.id = c.list_id
       ${where.length ? 'WHERE ' + where.join(' AND ') : ''}
       ORDER BY l.name ASC, c.card_order ASC, c.name ASC
       LIMIT 500
    `
    const { rows } = await query(sql, params)

    res.render('search', {
      title: 'Busca',
      results: rows,
      query: { q, condition, language, card_type, owned, grading_min, grading_max },
      LANGUAGES,
      CONDITIONS,
      CARD_TYPES,
    })
  } catch (e) { next(e) }
})

// Atualizar card (com troca de imagem opcional)
app.post('/card/:id', requireAuth, upload.single('photo'), async (req, res, next) => {
  try {
    const cardId = parseInt(req.params.id, 10)
    const { name, card_number, collection_total, language, condition, grading_note, owned, card_type } = req.body
    let photo_url = null
    if (req.file && req.file.buffer) {
      const result = await uploadBuffer(req.file.buffer, { filename: undefined, folder: 'pokelist' })
      photo_url = result.secure_url
    }
    if (photo_url) {
      await query(
        `UPDATE cards SET name=$1, card_number=$2, collection_total=$3, language=$4,
                          condition=$5, grading_note=$6, owned=$7, card_type=$8, photo_url=$9
           WHERE id=$10`,
        [name, card_number || null, collection_total || null, language || null,
         condition || null, grading_note ? parseInt(grading_note, 10) : null,
         owned === 'on', card_type || null, photo_url, cardId]
      )
    } else {
      await query(
        `UPDATE cards SET name=$1, card_number=$2, collection_total=$3, language=$4,
                          condition=$5, grading_note=$6, owned=$7, card_type=$8
           WHERE id=$9`,
        [name, card_number || null, collection_total || null, language || null,
         condition || null, grading_note ? parseInt(grading_note, 10) : null,
         owned === 'on', card_type || null, cardId]
      )
    }
    res.redirect(`/card/${cardId}`)
  } catch (e) { next(e) }
})

// Alternar status
app.post('/card/:id/toggle', requireAuth, async (req, res, next) => {
  try {
    const cardId = parseInt(req.params.id, 10)
    await query('UPDATE cards SET owned = NOT COALESCE(owned,false) WHERE id = $1', [cardId])
    res.redirect(`/card/${cardId}`)
  } catch (e) { next(e) }
})

// Criar novo card (com upload de imagem)
app.post('/list/:id/cards', requireAuth, upload.single('photo'), async (req, res, next) => {
  try {
    const listId = parseInt(req.params.id, 10)
    const { name, card_number, collection_total, language, condition, grading_note, owned, card_type } = req.body
    if (!name || !req.file || !req.file.buffer) {
      return res.status(400).send('Nome e imagem são obrigatórios')
    }
    const result = await uploadBuffer(req.file.buffer, { folder: 'pokelist' })
    const photoUrl = result.secure_url
    await query(
      `INSERT INTO cards (name, photo_url, card_number, collection_total, language, list_id,
                          card_order, condition, grading_note, owned, card_type)
       VALUES ($1, $2, $3, $4, $5, $6,
              (SELECT COALESCE(MAX(card_order),0)+1 FROM cards WHERE list_id=$6),
              $7, $8, $9, $10)`,
      [
        name, photoUrl, card_number || null, collection_total || null, language || null, listId,
        condition || null, grading_note ? parseInt(grading_note, 10) : null, owned === 'on', card_type || 'Normal',
      ]
    )
    res.redirect(`/list/${listId}`)
  } catch (e) { next(e) }
})

// Remover card
app.delete('/card/:id', requireAuth, async (req, res, next) => {
  try {
    const cardId = parseInt(req.params.id, 10)
    const { rows } = await query('DELETE FROM cards WHERE id=$1 RETURNING list_id', [cardId])
    const listId = rows[0]?.list_id || ''
    res.redirect(listId ? `/list/${listId}` : '/')
  } catch (e) { next(e) }
})

// Página de erro simples
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error(err)
  res.status(500).send('Erro interno')
})

app.listen(port, () => {
  console.log(`Pokélist JS rodando em http://localhost:${port}`)
})
