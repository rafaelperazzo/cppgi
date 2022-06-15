# -*- coding: utf-8 -*-
#import os
#command = "unoconv -f pdf -o /home/perazzo/cppgi/pdfs/certificado.pdf /home/perazzo/cppgi/pdfs/certificado.odt"
#s = os.popen(command).read()

#print(s)
import subprocess
#subprocess.call(["unoconv","-f","pdf","-o","/home/perazzo/cppgi/pdfs/certificado.pdf","/home/perazzo/cppgi/pdfs/certificado.odt"])
p = subprocess.Popen(["libreoffice","--convert-to","pdf:writer_pdf_Export","/home/perazzo/cppgi/pdfs/certificado.odt","--outdir","/home/perazzo/cppgi/pdfs/"],stdout=subprocess.PIPE)
s = p.communicate()
print(s)
