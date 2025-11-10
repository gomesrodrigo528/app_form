from flask import Blueprint, render_template, request, redirect, session, flash
from app.models import Form, FormField, FormSubmission, FormResponse, Lead, Tenant, TenantSettings
from datetime import datetime
import urllib.parse

bp = Blueprint('forms', __name__, url_prefix='/f')

@bp.route('/<tenant_slug>/<form_id>', methods=['GET', 'POST'])
def form_view(tenant_slug, form_id):
    """Visualização pública do formulário para leads"""
    
    # Buscar tenant
    tenant = Tenant.get_by_slug(tenant_slug)
    if not tenant:
        return render_template('errors/404.html', message='Empresa não encontrada'), 404
    
    # Buscar formulário
    form = Form.get_by_id(form_id)
    if not form or form['tenant_id'] != tenant['id'] or not form['is_active']:
        return render_template('errors/404.html', message='Formulário não encontrado'), 404
    
    # Buscar campos
    fields = FormField.get_by_form(form_id)
    
    # Buscar configurações
    settings = TenantSettings.get_by_tenant(tenant['id'])
    
    if request.method == 'POST':
        # Processar submissão
        phone = request.form.get('phone')
        email = request.form.get('email')
        name = request.form.get('name')
        
        # Criar ou buscar lead
        lead = Lead.get_or_create(tenant['id'], phone, email, name)
        if not lead:
            flash('Erro ao processar formulário. Tente novamente.', 'error')
            return render_template('forms/view.html', 
                                 form=form, 
                                 fields=fields, 
                                 tenant=tenant, 
                                 settings=settings)
        
        # Criar submissão
        submission = FormSubmission.create(form_id, lead['id'], tenant['id'])
        if not submission:
            flash('Erro ao processar formulário. Tente novamente.', 'error')
            return render_template('forms/view.html', 
                                 form=form, 
                                 fields=fields, 
                                 tenant=tenant, 
                                 settings=settings)
        
        # Salvar respostas e montar mensagem do WhatsApp
        whatsapp_message = f"🔔 *Nova Resposta de Formulário*\n\n"
        whatsapp_message += f"📋 *Formulário:* {form['title']}\n"
        whatsapp_message += f"👤 *Lead:* {name or 'Não informado'}\n"
        whatsapp_message += f"📱 *Telefone:* {phone or 'Não informado'}\n"
        whatsapp_message += f"📧 *Email:* {email or 'Não informado'}\n"
        whatsapp_message += f"\n{'─' * 30}\n\n"
        whatsapp_message += f"*📝 RESPOSTAS:*\n\n"
        
        for field in fields:
            field_id = field['id']
            field_name = f'field_{field_id}'
            
            # Processar valores de campos de múltipla seleção (checkboxes)
            if field['field_type'] == 'checkbox' and field.get('options'):
                response_values = request.form.getlist(f'{field_name}[]')
                response_value = ", ".join(response_values) if response_values else ''
            else:
                response_value = request.form.get(field_name, '')
            
            # Salvar no banco
            FormResponse.create(submission['id'], field_id, response_value)
            
            # Adicionar à mensagem do WhatsApp apenas se houver valor
            if response_value:
                whatsapp_message += f"▪️ *{field['label']}*\n"
                whatsapp_message += f"   {response_value}\n\n"
        
        # Adicionar rodapé com data/hora
        whatsapp_message += f"\n{'─' * 30}\n"
        whatsapp_message += f"🕐 *Enviado em:* {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        
        # Marcar submissão como completa
        FormSubmission.update(submission['id'], {
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        })
        
        # Preparar link do WhatsApp
        whatsapp_number = tenant['whatsapp_number']
        if whatsapp_number:
            # Remover caracteres não numéricos
            whatsapp_number = ''.join(filter(str.isdigit, whatsapp_number))
            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(whatsapp_message)}"
            
            # Marcar como enviado para WhatsApp
            FormSubmission.update(submission['id'], {
                'whatsapp_sent': True,
                'whatsapp_sent_at': datetime.now().isoformat()
            })
            
            # Redirecionar DIRETAMENTE para o WhatsApp
            return redirect(whatsapp_url)
        else:
            # Se não tiver WhatsApp configurado, mostrar página de sucesso
            flash('Formulário enviado com sucesso!', 'success')
            return render_template('forms/success.html', 
                                 whatsapp_url=None, 
                                 tenant=tenant, 
                                 settings=settings)
    
    return render_template('forms/view.html', 
                         form=form, 
                         fields=fields, 
                         tenant=tenant, 
                         settings=settings)
