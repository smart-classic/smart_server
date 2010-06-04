"""
Indivo Views -- Messaging
"""

from base import *

@transaction.commit_on_success
@paramloader()
def account_send_message(request, account):
  Message.objects.create( account             = account, 
                          sender              = request.principal, 
                          recipient           = account, 
                          external_identifier = request.POST.get('message_id', None), 
                          subject             = request.POST.get('subject', "[no subject]"), 
                          body                = request.POST.get('body', "[no body]"))
  # return the message ID? or just DONE
  return DONE

@paramloader()
@transaction.commit_on_success
def record_send_message(request, record, message_id):
  record.send_message(external_identifier = message_id, 
                      sender              = request.principal.effective_principal,
                      subject             = request.POST.get('subject', '[no subject]'), 
                      body                = request.POST.get('body',    '[no body]'))
  # probably the right thing to return
  return DONE

@paramloader()
@marsloader
def record_inbox(request, record, limit, offset, status, order_by='-received_at'):
  messages = record.get_messages().order_by(order_by)
  return render_template('messages', {'messages' : messages})

@paramloader()
@marsloader
def account_inbox(request, account, limit, offset, status, order_by='-received_at'):
  messages = account.message_as_recipient.order_by(order_by)
  return render_template('messages', {'messages' : messages})

@paramloader()
def account_inbox_message(request, account, message_id):
  message = account.message_as_recipient.get(id = message_id)
  return render_template('message', {'message' : message})

@paramloader()
@marsloader
def account_notifications(request, account, limit, offset, status, order_by='-created_at'):
  notifications = Notification.objects.filter(account = account).order_by(order_by)
  return render_template('notifications', {'notifications' : notifications})
