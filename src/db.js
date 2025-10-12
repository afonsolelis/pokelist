import dotenv from 'dotenv'
import pkg from 'pg'

// Ensure environment variables are loaded before reading them
dotenv.config()

const { Pool } = pkg

const connectionString = process.env.DATABASE_URL

export const pool = new Pool({
  connectionString,
  ssl: connectionString && connectionString.includes('supabase.com')
    ? { rejectUnauthorized: false }
    : undefined,
})

export async function query(text, params) {
  const client = await pool.connect()
  try {
    const res = await client.query(text, params)
    return res
  } finally {
    client.release()
  }
}
