rm ~/.streamlit/config.toml
mkdir ./.streamlit/
echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
[theme]\n\
primaryColor = '#d33682'\n\
backgroundColor = '#070f11'\n\
secondaryBackgroundColor = '#586e75'\n\
textColor = '#fff'\n\
" > ./.streamlit/config.toml