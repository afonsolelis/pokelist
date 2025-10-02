-- Altera o tipo da coluna collection_total para VARCHAR para suportar letras
ALTER TABLE cards ALTER COLUMN collection_total TYPE VARCHAR(20);
