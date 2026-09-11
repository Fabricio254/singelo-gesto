"""Catalogo de produtos importado do Instagram para a Singelo Gesto."""
from __future__ import annotations
import json
import streamlit as st
from Instagram import collect_profile, product_message, whatsapp_url

def format_brl(value):
    if value is None: return "Valor nao identificado"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def render_product(product, index, phone):
    col_image, col_data = st.columns([1, 2])
    with col_image:
        if product.get("image_url"): st.image(product["image_url"], use_container_width=True)
        else: st.info("Sem imagem")
    with col_data:
        title = st.text_input("Nome do produto", product.get("title", ""), key=f"title_{index}")
        categories = ["Cafe da manha", "Aniversario", "Maternidade", "Casamento e noivado", "Flores e mimos", "Datas especiais", "Outros"]
        current = product.get("category", "Outros")
        category = st.selectbox("Categoria", categories, index=categories.index(current) if current in categories else 6, key=f"category_{index}")
        price = st.number_input("Preco (R$)", min_value=0.0, value=float(product["price"]) if product.get("price") is not None else 0.0, step=0.01, key=f"price_{index}")
        description = st.text_area("Descricao da publicacao", product.get("description", ""), height=130, key=f"description_{index}")
        product.update({"title": title, "category": category, "price": price or None, "description": description})
        if product.get("prices_found"): st.caption("Precos encontrados: " + ", ".join(format_brl(item) for item in product["prices_found"]))
        st.link_button("Abrir no WhatsApp", whatsapp_url(phone, product_message(product)), use_container_width=True)
        if product.get("permalink"): st.link_button("Ver publicacao", product["permalink"], use_container_width=True)
def main():
    st.set_page_config(page_title="Catalogo Instagram | Singelo Gesto", page_icon="G", layout="wide")
    st.title("Catalogo do Instagram")
    st.caption("Importe as publicacoes, revise os precos e abra a mensagem pronta no WhatsApp.")
    with st.sidebar:
        st.header("Importar publicacoes")
        username = st.text_input("Usuario do Instagram", "singelo_gesto")
        password = st.text_input("Senha do Instagram", type="password")
        amount = st.number_input("Quantidade de publicacoes", min_value=1, max_value=200, value=40, step=10)
        phone = st.text_input("WhatsApp do cliente", placeholder="(27) 99999-9999")
        import_button = st.button("Importar do Instagram", type="primary", use_container_width=True)
        st.caption("A senha fica somente nesta sessao e nao e gravada no codigo.")
    if import_button:
        if not username or not password: st.error("Informe o usuario e a senha.")
        else:
            with st.spinner("Acessando o Instagram e lendo as publicacoes..."):
                try:
                    st.session_state.catalog_products = collect_profile(username.strip().lstrip("@"), password, int(amount))
                    st.success(f"{len(st.session_state.catalog_products)} publicacoes importadas.")
                except Exception as exc:
                    st.error(f"Nao foi possivel importar: {exc}")
                    st.info("O Instagram pode pedir confirmacao de login. Confirme no aplicativo e tente novamente.")
    products = st.session_state.get("catalog_products", [])
    if not products:
        st.info("Use o painel ao lado para importar os produtos do perfil.")
        return
    search = st.text_input("Buscar produto ou categoria", placeholder="Ex.: aniversario, cafe, caneca")
    query = search.lower().strip()
    filtered = [item for item in products if not query or query in (item.get("title", "") + " " + item.get("category", "") + " " + item.get("description", "")).lower()]
    st.write(f"{len(filtered)} produto(s) exibido(s)")
    for index, product in enumerate(filtered):
        with st.expander(f"{product.get('title', 'Produto')} | {format_brl(product.get('price'))}", expanded=index == 0):
            render_product(product, index, phone)
    st.download_button("Baixar catalogo revisado (JSON)", data=json.dumps(products, ensure_ascii=False, indent=2, default=str), file_name="catalogo_singelo_gesto.json", mime="application/json", use_container_width=True)
if __name__ == "__main__":
    main()
