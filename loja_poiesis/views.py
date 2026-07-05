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
            data = json.loads(request.body)
            price = data.get('price', 3990)
            name = data.get('name', 'Coleção')
            # Define o identificador do produto para o webhook (usaremos no metadata)
            product_id = data.get('product_id', 'colecao')
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': name,
                        },
                        'unit_amount': price,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://poiesis-loja-production.up.railway.app/sucesso',
                cancel_url='https://poiesis-loja-production.up.railway.app/biblioteca',
                metadata={
                    'product': product_id  # ex: 'patior', 'icaro', 'colecao'
                }
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
    endpoint_secret = 'whsec_LHm4EvuZegGLPvcLAytzKJezVOI8MDIa'  # Substitua pelo segredo real depois

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
            # Obtém o nome do produto a partir dos metadados da sessão
            product = session.get('metadata', {}).get('product', 'colecao')
            
            # Mapeia o product para o caminho do PDF
            pdf_map = {
                'patior': settings.BASE_DIR / 'pdfs' / 'patior.pdf',
                'icaro': settings.BASE_DIR / 'pdfs' / 'icaro.pdf',
                'mulherar': settings.BASE_DIR / 'pdfs' / 'mulherar.pdf',
                'desajeitados': settings.BASE_DIR / 'pdfs' / 'desajeitados.pdf',
                'poiesis': settings.BASE_DIR / 'pdfs' / 'poiesis_livro_i.pdf',
                'colecao': settings.BASE_DIR / 'pdfs' / 'colecao_primeiros_voos.pdf',
            }
            pdf_path = pdf_map.get(product)

            if pdf_path and pdf_path.exists():
                email = EmailMessage(
                    'Sua travessia começa aqui | Poiesis',
                    'Obrigado por adquirir seu livro. O PDF segue em anexo.\n\nCom afeto,\nCarlos Eduardo',
                    'duducecg2006@gmail.com',  # seu e‑mail verificado no SendGrid
                    [customer_email],
                )
                email.attach_file(pdf_path)
                email.send(fail_silently=False)
            else:
                print(f"PDF não encontrado para o produto: {product}")

    return HttpResponse(status=200)