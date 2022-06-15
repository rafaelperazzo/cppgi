curl "https://sci01-ter-jne.ufca.edu.br/cppgi/certificadoModerador?id=7" 
sudo chown perazzo:www-data *
chmod 770 *
unoconv -f pdf MODERADOR*.odt
sudo chown perazzo:www-data *
chmod 770 *
rm *.bak
