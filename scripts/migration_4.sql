-- Altera o tipo da coluna card_number para VARCHAR para suportar letras
ALTER TABLE cards ALTER COLUMN card_number TYPE VARCHAR(20);

-- Permite que a coluna collection_total seja nula
ALTER TABLE cards ALTER COLUMN collection_total DROP NOT NULL;
