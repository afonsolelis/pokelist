-- Atualiza a constraint de condição para incluir 'GM' (Gem Mint) e 'M' (Mint)
ALTER TABLE cards DROP CONSTRAINT IF EXISTS cards_condition_check;
ALTER TABLE cards ADD CONSTRAINT cards_condition_check CHECK (condition IN ('GM', 'M', 'NM', 'SP', 'MP', 'HP', 'D'));

