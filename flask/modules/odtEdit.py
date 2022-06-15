from ezodf import newdoc
import os
import zipfile
import tempfile
namef = '/home/perazzo/cppgi/documentos/certificado.odt'
odt = newdoc(doctype='odt', filename=namef, template='/home/perazzo/cppgi/documentos/07-certificado.apresentacao.odt')
odt.save()
a = zipfile.ZipFile('/home/perazzo/cppgi/documentos/07-certificado.apresentacao.odt')
content = a.read('/home/perazzo/cppgi/documentos/content.xml')
content = str(content.decode(encoding='utf8'))
content = str.replace(content,"PERAZZO", '123')
content = str.replace(content, 'RAFAEL', '456')



def updateZip(zipname, filename, data):
    # generate a temp file
    tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
    os.close(tmpfd)

    # create a temp copy of the archive without filename
    with zipfile.ZipFile(zipname, 'r') as zin:
        with zipfile.ZipFile(tmpname, 'w') as zout:
            zout.comment = zin.comment # preserve the comment
            for item in zin.infolist():
                if item.filename != filename:
                    zout.writestr(item, zin.read(item.filename))

    # replace with the temp archive
    os.remove(zipname)
    os.rename(tmpname, zipname)

    # now add filename with its new data
    with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)

updateZip(namef, '/home/perazzo/cppgi/documentos/content.xml', content)
