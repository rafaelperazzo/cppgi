curl "https://sci02-ter-jne.ufca.edu.br/cppgi/certificadoApresentacao?id=7" 
chown perazzo:www-data *
chmod 770 *
unoconv -f pdf certificado*.odt
chown perazzo:www-data *
chmod 770 *
rm *.bak
