-- Banco separado para a suíte de testes (docs/guia/testes.md).
-- Só roda na primeira subida, com o volume postgres_data vazio. Com volume já existente:
--   docker compose exec db createdb -U itam itam_test
CREATE DATABASE itam_test;
