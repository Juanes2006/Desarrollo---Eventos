from flask import render_template, redirect, url_for, flash,request
from . import super_admin_bp
from models import db, Evento


@super_admin_bp.route('/super_admin', methods=['GET', 'POST'])
def super_admin():
    if request.method == "POST":
        pass
    eventos = Evento.query.all()
    return render_template("super_admin.html", eventos=eventos)





@super_admin_bp.route('/eventos', methods=['GET','POST'])
def eventos_superadmin():
    eventos = Evento.query.all()
    return render_template("super_admin.html", eventos=eventos)

@super_admin_bp.route('/evento/<int:eve_id>')
def ver_evento_superadmin(eve_id):
    evento = Evento.query.get_or_404(eve_id)
    return render_template('detalle_evento_superadmin.html', evento=evento)
