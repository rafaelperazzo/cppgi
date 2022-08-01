function salvar(elemento) {
    var dados = elemento.serializeArray();
    var valor = dados[0].value;
    var coluna_id = dados[0].name.split("_");
    var coluna = coluna_id[0];
    var form_id = elemento.get(0).form.id;
    var str = form_id.split("_");
    var identificador = coluna_id[1];
    var tabela = str[2];
    var action = "/salvar" + "/" + String(tabela) + "/" + identificador + "/" + coluna + "/" + valor;
    $.get(action,function(data) {
    });
}

function detalhes(elemento) {
    var linha = elemento.closest("tr");
    var id_linha = linha.attr("id");
    var id = id_linha.split("_")[1];
    $("#botao_detalhes").click();
    $("#campo_detalhes").val(elemento.val());
    $("#detalhes_id").text(id);
    var coluna_id = elemento.attr("name").split("_");
    $("#coluna").val(coluna_id[0]);
}

function salvar_detalhes(elemento) {
    var tabela = $("#tabela").val();
    var identificador = $("#detalhes_id").text();
    var coluna = $("#coluna").val();
    var valor = $("#campo_detalhes").val();
    var action = "/salvar" + "/" + String(tabela) + "/" + identificador + "/" + coluna + "/" + valor;
    $.get(action,function(data) {        
    });
    var nome_campo = "#" + String(coluna) + "_" + String(identificador);
    $(nome_campo).val(valor);
}

$(document).ready(function(){
    $(".campo").on("change",function(event){
        salvar($(this));
    });
    $(".campo").on("dblclick",function(event){
        detalhes($(this));
    });
    $(".campo_modal").on("change",function(event){
        salvar_detalhes($(this));
    });
});