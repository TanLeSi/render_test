mkdir -p .streamlit
echo -e "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
\n\
" > .streamlit/config.toml