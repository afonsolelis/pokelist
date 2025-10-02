-- Adiciona as colunas de estado da carta e nota de graduação
ALTER TABLE cards
ADD COLUMN grading_note INTEGER,
ADD COLUMN condition VARCHAR(3) CHECK (condition IN ('NM', 'SP', 'MP', 'HP', 'D'));

-- Define um valor padrão para a condição das cartas existentes
UPDATE cards SET condition = 'NM' WHERE condition IS NULL;

-- Torna a coluna de condição não-nula
ALTER TABLE cards
ALTER COLUMN condition SET NOT NULL;
