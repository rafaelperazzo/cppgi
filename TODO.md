# TODO

## Submissões

- [ ] Ajustar largura do template `submissoes.html` assim como está em `editalProjeto.html`

- [ ] Implementar edição dos dados do projeto
  - Adicionar botão "Editar" na coluna de ações da tabela de `submissoes.html` (ao lado do botão de remoção)
  - Criar rota `GET/POST /editar_submissao/<id_projeto>` em `pesquisa.py`
  - Criar template `editarSubmissao.html`

- [ ] Ajustar coluna de avaliações em `submissoes.html`
  - Revisar/formatar os dados exibidos na célula de avaliações
  - Adicionar botão de edição por linha de avaliação → rota `GET/POST /edicao_avaliacao/<id_avaliacao>` + template `edicaoAvaliacao.html`
  - Adicionar botão de remoção por linha de avaliação → rota `GET /remover_avaliacao_submissao/<id_avaliacao>/<edital>`
