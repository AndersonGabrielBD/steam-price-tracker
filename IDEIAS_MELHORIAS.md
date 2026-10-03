# Ideias de melhoria — Steam Price Tracker

Objetivo: sair de "projeto que funciona" para "projeto que um recrutador técnico olha e entende, em 2 minutos, que quem fez isso sabe construir sistema de verdade". Dividido por frente, com prioridade e esforço estimado. Não precisa fazer tudo — ver seção "Por onde eu começaria" no fim.

Legenda: 🔥 alto impacto para recrutador · ⚙️ esforço (P pequeno / M médio / G grande)

---

## 1. Deploy ao vivo (isso é o item mais importante da lista)

Hoje o projeto só roda se alguém clonar e subir Docker. Recrutador não vai fazer isso — ele clica em um link, ou não vê nada.

- **❌ Deploy público — decisão consciente de não fazer** (pesquisado, não esquecido): investiguei Railway e AWS antes de descartar. Railway removeu o tier gratuito indefinido em favor de um crédito único de $5/30 dias, depois $5/mês mínimo. AWS trocou (jul/2025) os 12 meses grátis de EC2/RDS por um crédito único de $200/6 meses — depois disso volta a cobrar; a parte realmente "sempre grátis" da AWS é só Lambda/DynamoDB, o que exigiria reescrever o projeto em serverless e jogar fora a demonstração de Celery. Para um projeto-demonstração, não fez sentido pagar mensalidade recorrente por um link. Decisão e trade-off completo documentados no README (seção "Por que não tem um link ao vivo"); o investimento foi redirecionado para `docker compose up` em 2 comandos + README com prints reais e decisões de arquitetura explicadas.
- **✅ Seed de dados** (⚙️ P, implementado): `backend/scripts/seed.py` popula 12 jogos populares (CS2, GTA V Enhanced, Elden Ring, Hollow Knight, Stardew Valley, Hades, Cyberpunk 2077, RDR2, Baldur's Gate 3, Portal 2, Terraria, Celeste), reaproveitando o mesmo fluxo de add+backfill da API. Idempotente (`docker compose exec api python -m scripts.seed`).

Sem deploy, o README precisa carregar mais peso: prints reais, GIF/fluxo e as decisões de arquitetura explicadas são o que substitui o link clicável.

## 2. Visual (hoje provavelmente está genérico — isso é o que "brilha o olho")

- **✅ Capa dos jogos** (⚙️ P, implementado): a Steam API já retorna `header_image` no `appdetails` — agora é parseado em `steam_client.py` e exibido no card (`GameList.jsx`).
- **✅ Badge de menor preço histórico** (⚙️ M, implementado): `is_all_time_low` calculado no backend (`_is_all_time_low` em `routers/games.py`, compara o preço atual com o mínimo já registrado) e exibido como selo "🔥 Menor preço histórico" no card.
- **✅ Gráfico mais rico** (⚙️ P, implementado): `AreaChart` com gradiente, `ReferenceDot` marcando o menor preço, tooltip customizado com % de desconto vs. preço cheio, e diferenciação visual entre pontos `steam_live` e `itad_backfill`.
- **✅ Estado vazio ilustrado** (⚙️ P, implementado): tela com ícone e chamada para ação quando não há jogos ou não há histórico.
- **✅ Loading states** (⚙️ P, implementado): skeleton com shimmer na lista enquanto carrega.
- **✅ Ordenação e filtro** (⚙️ P, implementado): `GET /games` aceita `sort` (added_at/name/price/discount), `order` e `on_sale_only`, com controles na UI.
- **Responsivo mobile** (⚙️ P): CSS ajustado, mas não testado em viewport real neste ambiente (ferramenta de resize da sessão não funcionou) — vale confirmar manualmente no celular.

## 3. Features que mostram profundidade de backend (não só CRUD)

- **🔥 Alertas de preço por e-mail** (⚙️ M): usuário define um preço-alvo por jogo; quando o Celery detecta que bateu, dispara um e-mail (Resend/SendGrid free tier). Isso transforma o projeto de "mostra gráfico" para "sistema que age sozinho" — é o tipo de feature que demonstra entender fila assíncrona de verdade, não só "porque o tutorial usa Celery".
- **🔥 Cache de chamadas à Steam com Redis** (⚙️ P): hoje toda checagem bate direto na Steam. Cachear resposta por alguns minutos (`SETEX`) evita rate-limit e mostra uso de Redis além do pub/sub — detalhe que entrevistador de backend pleno/sênior pergunta direto ("por que você colocou cache aqui?").
- **Rate limiting na API** (⚙️ P, lib `slowapi`): mostra que pensou em abuso/produção, não só no "caminho feliz".
- **Importar lista de jogos da Steam** (⚙️ G): dado um `steamid` ou vanity URL público, importar a wishlist/biblioteca automaticamente em vez de adicionar um por um. É a feature mais "uau" da lista, mas também a mais trabalhosa (precisa lidar com perfis privados, paginação da Steam).
- **Ordenação e filtros** (⚙️ P): ordenar por maior desconto, nome, preço — trivial de implementar, mas é o tipo de coisa que falta em projeto de portfólio e fica óbvio quando falta.
- **Exportar histórico em CSV** (⚙️ P): endpoint simples, mas comunica "pensei no usuário querer os dados dele".
- **✅ Backfill de histórico via IsThereAnyDeal** (⚙️ M, implementado): a API da Steam só dá o preço atual — não tem histórico oficial. O [IsThereAnyDeal](https://docs.isthereanydeal.com/) já rastreia preço de várias lojas há anos e expõe isso via API gratuita (`games/history/v2`). Testado empiricamente contra a API real: filtrando por `shops=61` (id da Steam no ITAD) + `country=br`, o preço vem **sempre em BRL** — sem mistura de moeda, então não precisou de nenhuma lógica de conversão/rotulagem. Ao cadastrar um jogo, o backend já importa automaticamente os últimos ~3 meses de preço real da Steam (`app/itad_client.py` + `_backfill_history` em `app/routers/games.py`), marcando as linhas com `source="itad_backfill"` vs. `source="steam_live"` nas checagens do Celery. Bom gancho de entrevista: "fonte primária vs. fonte de backfill" em vez de inventar dado mockado.

## 4. Mentalidade de produção (o que diferencia pleno/sênior de júnior nas perguntas de entrevista)

- **✅ Health check** (⚙️ P, implementado): `/health` testa Postgres (`SELECT 1`) e Redis (`PING`) de verdade, retorna 503 se algo falhar.
- **✅ Logging estruturado** (⚙️ M, implementado): `structlog` em JSON com `request_id` por requisição, na API e no worker/beat.
- **✅ Rate limiting** (⚙️ P, implementado): `slowapi`, 10/min em `POST /games` e 20/min em `/games/search` — as duas rotas que chamam Steam/ITAD. Testado de verdade: a 21ª chamada em sequência à busca retorna 429.
- **✅ Export CSV** (⚙️ P, implementado): `GET /games/{id}/history.csv` com todo o histórico de preço, incluindo a coluna `source` (steam_live vs. itad_backfill).
- **✅ Cobertura de testes** (⚙️ P, implementado): `pytest-cov`, 78% de cobertura, badge estático no README. **Nota:** cogitei automatizar a geração do badge via `coverage-badge` + commit automático no CI, mas descartei — a lib depende de `pkg_resources` (obsoleta, exigiria pin de `setuptools<81`) e o auto-commit no `main` a cada run é um tipo de automação que prefiro não ligar sem confirmação explícita. Badge é estático por enquanto; atualizar manualmente quando a cobertura mudar bastante.
- **✅ Dependabot** (⚙️ P, implementado): `.github/dependabot.yml` cobrindo pip, npm, GitHub Actions e Docker (backend+frontend).
- **Métricas com Prometheus + um dashboard Grafana simples** (⚙️ G): quantas checagens de preço por minuto, latência da Steam API, taxa de erro. É um diferencial forte para vaga de backend, mas é o item mais caro da lista — só vale se já tiver o resto pronto. Deixado como próximo passo no roadmap do README.

## 5. Storytelling do README (o recrutador lê o README antes de rodar qualquer coisa)

- **✅ Prints reais do app rodando** (⚙️ P, implementado): capturados via Playwright direto da stack local rodando em Docker (não mockup) — visão geral, painel de detalhe com gráfico, tooltip com fonte do dado, busca com autocomplete, responsivo mobile, documentação Swagger. Em `docs/screenshots/`.
- **✅ Seção "Decisões de arquitetura"** (⚙️ P, implementado): por que Redis faz três papéis (fila do Celery + pub/sub + cache), por que Beat e Worker são processos separados, por que `Base.metadata.create_all` ficou no lifespan e não no import, por que `PriceAlert` é tabela própria, por que `source` é campo explícito em vez de dado misturado, por que rate limit só nas rotas que chamam API externa, por que o health check é de verdade.
- **✅ Diagrama de arquitetura como imagem** (⚙️ P, implementado): gerado com Mermaid CLI (`docs/screenshots/architecture.png`), tema escuro, no lugar do ASCII antigo.
- **✅ Seção "Por que construí isso"** (⚙️ P, implementado).
- **✅ Seção "Por que não tem um link ao vivo"** (⚙️ P, implementado — não estava na lista original): como não houve deploy (ver item 1), virou parte da narrativa em vez de ficar escondido — explica o trade-off de custo pesquisado (Railway, AWS) e por que não compensou para um projeto-demonstração.
- GIF do fluxo real (cadastrar → preço aparece → gráfico atualiza via WebSocket): não implementado ainda — prints estáticos já cobrem o essencial; fica como possível próximo passo.

## 6. Itens que eu NÃO priorizaria agora

- Autenticação multi-usuário — vira outro projeto inteiro (login, sessão, isolamento de dados). Só vale se o resto já estiver pronto e sobrar tempo.
- Previsão de preço com ML — fácil de prometer, fácil de ficar com cara de "achismo" se não tiver dado suficiente. Risco de parecer over-engineering sem ganho real.
- Dark/light theme toggle — a Steam é dark por natureza, não agrega.

---

## Status atual (atualizado após a decisão de não fazer deploy)

1. ✅ Backfill histórico (ITAD) + seed de dados.
2. ✅ Capa dos jogos + badge de menor preço histórico + ordenação/filtro.
3. ✅ Cache Redis + health check real + logging estruturado + rate limiting.
4. ❌ Deploy ao vivo — decisão consciente de não fazer (ver item 1 e README).
5. ✅ README com prints reais, diagrama de arquitetura, decisões explicadas e a própria decisão de não fazer deploy documentada como parte da narrativa.
6. ⏳ Alertas de preço por e-mail — não implementado; tabela `PriceAlert` já existe no schema, mas o fluxo (CRUD + Resend) ficou de fora por escopo. Único item verdadeiramente pendente, e é opcional.

O resto (Prometheus/Grafana, import de wishlist, multi-usuário) fica como "próximos passos" no README — menciona que pensou neles, sem precisar construir tudo agora.
