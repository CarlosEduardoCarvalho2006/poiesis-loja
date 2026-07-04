import json
import stripe
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage

# Configura a chave secreta do Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# --- Páginas do site ---

def home(request):
    return render(request, 'index.html')

def biblioteca(request):
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'biblioteca.html', context)

def atendimento(request):
    return render(request, 'atendimento.html')

def sucesso(request):
    return render(request, 'sucesso.html')

# --- Checkout do Stripe ---

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': 'Coleção Primeiros Voos',
                        },
                        'unit_amount': 3990,  # R$39,90 em centavos
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='http://127.0.0.1:8000/sucesso',
                cancel_url='http://127.0.0.1:8000/biblioteca',
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Método não permitido'}, status=405)

# --- Webhook do Stripe (entrega do PDF) ---

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = 'whsec_SEU_SEGREDO_AQUI'  # Substitua pelo segredo real depois

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Quando o checkout é concluído
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_details', {}).get('email')

        if customer_email:
            # Descomente e configure estas linhas quando o e-mail estiver pronto
            # email = EmailMessage(
            #     'Sua travessia começa aqui | Poiesis',
            #     'Obrigado por adquirir a Coleção Primeiros Voos. Clique no link para baixar: [LINK_DO_PDF]',
            #     'duducecg2006@gmail.com',
            #     [customer_email],
            # )
            # email.attach_file('static/livros/colecao_primeiros_voos.pdf')
            # email.send()
            
            # Por enquanto, apenas registramos no terminal
            print(f"Pagamento confirmado para {customer_email}. PDF seria enviado aqui.")

    return HttpResponse(status=200)