-- Cria a tabela de listas se ela não existir
CREATE TABLE IF NOT EXISTS lists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Cria a tabela de cards se ela não existir
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    photo_url VARCHAR(255) NOT NULL,
    card_number INT NOT NULL,
    collection_total INT NOT NULL,
    language VARCHAR(50) NOT NULL,
    list_id INT NOT NULL,
    CONSTRAINT fk_list
        FOREIGN KEY(list_id) 
        REFERENCES lists(id)
        ON DELETE CASCADE
);

-- Adiciona a coluna de ordenação se ela não existir (versão 2)
DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='cards' AND column_name='card_order') THEN
        ALTER TABLE cards ADD COLUMN card_order INTEGER;
    END IF;
END $$;

-- Define um valor inicial para a ordem dos cards existentes, caso seja nulo (versão 2)
UPDATE cards SET card_order = id WHERE card_order IS NULL;