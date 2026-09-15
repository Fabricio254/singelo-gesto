# Memoria do projeto Singelo Gesto

Este arquivo registra o estado funcional e as decisoes importantes do sistema. Leia antes de alterar o catalogo, a integracao com Instagram, o Supabase ou os links publicados.

## Visao geral

O projeto e o sistema de gestao de vendas e compras da Singelo Gesto, empresa de boxes de luxo personalizadas. A aplicacao administrativa roda em Streamlit e usa o Supabase como banco de dados. O catalogo enviado aos clientes e uma pagina HTML publica, hospedada no GitHub Pages pelo dominio oficial.

## Repositorios e publicacao

- Sistema administrativo/Streamlit: https://github.com/Fabricio254/singelo-gesto.git
- Aplicacao Streamlit: https://brfoyobozvbmtj76aafaed.streamlit.app/
- Site oficial: https://www.singelogesto.com.br/
- Repositorio do site oficial: https://github.com/Fabricio254/singelo-gesto-landing.git
- Catalogo publico atual: https://www.singelogesto.com.br/catalogo/
- O GitHub Pages do site oficial usa a branch main, a raiz do repositorio e o CNAME www.singelogesto.com.br.

O catalogo antigo em fabricio254.github.io pode continuar acessivel por cache ou pelo repositorio anterior, mas os links novos para clientes devem sempre usar https://www.singelogesto.com.br/catalogo/.

## Arquivos principais

- app.py: sistema Streamlit, menu administrativo, importacao/revisao do catalogo, links por categoria e catalogo publico legado.
- Instagram.py: importacao manual de links, normalizacao dos links, fallback quando o Instagram bloqueia a leitura e montagem da mensagem de WhatsApp.
- catalogo_instagram.py: funcoes auxiliares relacionadas ao catalogo.
- catalogo/index.html: pagina publica do catalogo HTML.
- catalogo/styles.css: estilos do catalogo HTML.
- catalogo/script.js: leitura dos produtos no Supabase, filtros, exibicao e links de WhatsApp.
- criar_tabela_catalogo_instagram.sql: criacao/estrutura da tabela do catalogo.
- corrigir_rls_catalogo_instagram.sql: politicas RLS necessarias para o catalogo.
- requirements.txt: dependencias Python.

## Banco de dados

- Projeto Supabase: fjgugglxqyhlyxwzvdts.
- Tabela principal do catalogo: singelo_catalogo_instagram.
- O frontend usa somente a chave anon/public configurada no codigo publico; nunca colocar service role key no HTML, no JavaScript ou no repositorio.
- A tabela precisa permitir leitura anonima dos produtos ativos para o catalogo publico.
- A importacao administrativa precisa permitir insercao, atualizacao e exclusao conforme as politicas definidas em corrigir_rls_catalogo_instagram.sql.
- Quando ocorrer erro new row violates row-level security policy, executar o SQL de correcao no SQL Editor do Supabase.

Campos usados pelo catalogo: id, title, category, description, price, image_url, image_urls, permalink e active.

## Categorias atuais

As categorias usadas no sistema sao:

- Aniversario
- Cafe da manha
- Maternidade
- Casamento e noivado
- Flores e mimos
- Datas especiais
- Outros

Regra de negocio: o filtro Casamento e noivado tambem apresenta produtos de Flores e mimos, pois as mesmas fotos de flores e mimos podem ser usadas para ocasiao de casamento. Essa regra existe no Streamlit e no catalogo/script.js por meio de alias de categoria.

Distribuicao registrada depois do pente fino:

- Aniversario: 21
- Cafe da manha: 36
- Maternidade: 17
- Flores e mimos: 32
- Datas especiais: 4
- Casamento e noivado: 1
- Outros: 0

Esses totais podem mudar quando novos produtos forem importados.

## Precos e descricoes

- O valor deve ficar no campo price, formatado como moeda brasileira no catalogo.
- A descricao nao deve repetir o preco quando ele ja esta em price.
- O catalogo remove precos duplicados da descricao antes de exibir ou enviar a mensagem.
- A mensagem de WhatsApp limita os detalhes da descricao a 300 caracteres.
- Produtos sem preco devem mostrar Consulte o valor.
- Na ultima revisao, havia dois produtos sem preco detectado: Simplesmente, linda! e E o dia dos Pais, foi lindo!. Conferir antes de inventar valores.

## Importacao de produtos

O Instagram pode bloquear a leitura automatica. Por isso o fluxo principal aceita colar varios links publicos e cria um produto de fallback pelo link, permitindo revisar titulo, categoria, valor, descricao, foto e status no Streamlit.

Ao adicionar produto novo:

1. Copiar o link permanente da publicacao do Instagram.
2. Colar o link no painel de Catalogo Instagram do Streamlit.
3. Deixar a busca automatica marcada apenas quando for desejado tentar obter descricao/foto do Instagram.
4. Importar e salvar.
5. Revisar categoria, titulo, price, descricao, imagem e checkbox de catalogo publico.
6. Salvar a edicao e testar o catalogo HTML.

Os links sao normalizados removendo parametros stkn, mas o permalink publico deve continuar apontando para a publicacao original.

## WhatsApp

O botao Quero esta opcao do catalogo HTML e do catalogo Streamlit abre o WhatsApp comercial da Singelo Gesto com uma mensagem contendo produto, categoria, valor, link da publicacao no Instagram, descricao curta e pedido de data e cidade de entrega.

O texto enviado precisa permanecer em ASCII simples para evitar caracteres quebrados no WhatsApp. Nao reintroduzir emojis ou simbolos decorativos na mensagem sem testar no celular, porque isso ja causou caracteres estranhos no atendimento.

Numero configurado no fluxo atual: 5527998622049.

## Catalogo HTML

O catalogo HTML busca os produtos ativos diretamente do Supabase no navegador. O cliente pode filtrar por ocasiao e clicar em Quero esta opcao. O link de cada categoria deve seguir este formato:

https://www.singelogesto.com.br/catalogo/?categoria=Aniversario

Para categoria com espacos, usar URL encoding, por exemplo Cafe%20da%20manha.

Para alterar o catalogo HTML, manter responsividade, a regra de casamento que inclui Flores e mimos, a limpeza de caracteres e o limite de 300 caracteres no WhatsApp. Tambem manter escape de texto/atributos antes de inserir dados do Supabase no HTML e validar com node --check catalogo/script.js.

Depois, publicar no repositorio singelo-gesto-landing e aguardar o GitHub Pages atualizar.

## Links no Streamlit

Os links para clientes sao montados por app.py usando o dominio oficial www.singelogesto.com.br. Se o painel ainda mostrar fabricio254.github.io ou o endereco do Streamlit, aguardar o redeploy, atualizar com F5, conferir se o campo de endereco publicado nao manteve valor antigo na sessao e verificar se catalog_public_base aponta para https://www.singelogesto.com.br/catalogo/.

## Procedimento de alteracao e verificacao

Antes de editar, verificar git status e preservar alteracoes do usuario. Depois de editar, validar Python com python -m py_compile app.py Instagram.py quando aplicavel, validar JavaScript com node --check catalogo/script.js, conferir a URL publicada e testar pelo menos uma categoria e um botao de WhatsApp.

Nunca registrar chaves, tokens ou senhas no AGENTS.md, commits ou mensagens.

## Decisoes ja tomadas

- O catalogo para clientes sera HTML no dominio oficial, por ser mais profissional e independente da interface administrativa do Streamlit.
- O Streamlit continua sendo o painel interno para importar, revisar, categorizar, alterar valores e ativar/desativar produtos.
- A separacao por ocasiao e feita pelo campo category, com a excecao documentada de Casamento e noivado incluir Flores e mimos.
- Alteracoes de valor devem ser feitas no campo proprio price; a descricao serve para os detalhes do produto.