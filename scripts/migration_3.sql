-- Adiciona a coluna 'owned' para marcar se o usuário possui o card
ALTER TABLE cards ADD COLUMN owned BOOLEAN NOT NULL DEFAULT true;
