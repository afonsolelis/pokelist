-- Adiciona coluna card_type com constraint de valores permitidos
-- Valores permitidos: Normal, Foil, Reverse Foil, Assinada, Promo, Textless, Alterada, Pre Release, Edition One, Shadowless, Staff, Misprint, Shattered Holo, Master Ball, Poke Ball

ALTER TABLE cards ADD COLUMN IF NOT EXISTS card_type VARCHAR(20);

-- Preenche valor padrão para registros existentes
UPDATE cards SET card_type = 'Normal' WHERE card_type IS NULL;

-- Garante not null após popular existentes
ALTER TABLE cards ALTER COLUMN card_type SET NOT NULL;

-- Cria/atualiza a constraint de domínio dos valores permitidos
ALTER TABLE cards DROP CONSTRAINT IF EXISTS cards_card_type_check;
ALTER TABLE cards ADD CONSTRAINT cards_card_type_check CHECK (
    card_type IN (
        'Normal', 'Foil', 'Reverse Foil', 'Assinada', 'Promo', 'Textless', 'Alterada', 'Pre Release', 'Edition One', 'Shadowless', 'Staff', 'Misprint', 'Shattered Holo', 'Master Ball', 'Poke Ball'
    )
);


