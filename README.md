# Gerenciador de Listas de Cards Pokémon

Este é um aplicativo web construído com Streamlit para ajudar colecionadores de cards de Pokémon a gerenciar suas coleções de forma digital.

## Funcionalidades

- **Gerenciamento de Listas**: Crie, renomeie e delete listas de cards.
- **Adição de Cards**: Adicione novos cards às suas listas, incluindo informações como nome, número, idioma e uma foto do card.
- **Visualização e Reordenação**: Visualize todos os cards em uma lista e reordene-os facilmente.
- **Busca Global**: Procure por um card em todas as suas listas para verificar se você já o possui.
- **Zoom de Imagem**: Clique para ampliar a imagem de um card e ver mais detalhes.

## Tecnologias Utilizadas

- **Backend**: Python
- **Frontend**: Streamlit
- **Banco de Dados**: PostgreSQL
- **Hospedagem de Imagens**: Cloudinary

## Configuração e Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/afonsolelis/pokelist.git
    cd pokelist
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**
    - Renomeie o arquivo `.env.example` para `.env`.
    - Preencha as variáveis no arquivo `.env`:
        - `DATABASE_URL`: A URL de conexão com seu banco de dados PostgreSQL.
        - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`: Suas credenciais do Cloudinary para o upload de imagens.

## Migração do Banco de Dados

Antes de iniciar o aplicativo, você precisa criar as tabelas no seu banco de dados PostgreSQL. Execute o script SQL encontrado em `scripts/migration.sql`.

## Como Executar

Com o ambiente configurado e o banco de dados migrado, inicie o aplicativo com o seguinte comando:

```bash
streamlit run app.py
```
