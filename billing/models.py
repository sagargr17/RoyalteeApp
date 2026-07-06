# billing/models.py
# python manage.py tenant_command createsuperuser --schema=public


from django.db import models
import uuid
import random


class Customer(models.Model):
    customer_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    access_pin = models.CharField(max_length=6, unique=True, editable=False, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)  # no longer required for auth
    created_at = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        if not self.access_pin:
            self.access_pin = self.generate_access_pin()
        super().save(*args, **kwargs)
        # generate QR after save so we have a pk and customer_code
        if not self.qr_code:
            self.generate_and_save_qr()

    def generate_customer_code(self):
        while True:
            code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
            if not Customer.objects.filter(customer_code=code).exists():
                return code

    def generate_access_pin(self):
        while True:
            pin = str(random.randint(1000, 9999))
            if not Customer.objects.filter(access_pin=pin).exists():
                return pin

    def generate_and_save_qr(self):
        try:
            import qrcode
            from qrcode.image.styledpil import StyledPilImage
            from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
            from PIL import Image, ImageDraw, ImageFont
            from io import BytesIO
            from django.core.files.base import ContentFile
            from django.db import connection

            schema = connection.schema_name

            # --- QR code generation (golden modules on white) ---
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(f"http://{schema}.localhost:8000/verify/?c={self.customer_code}")
            qr.make(fit=True)

            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                back_color=(255, 255, 255),
                fill_color="gold",  # golden color
            ).convert('RGBA')

            qr_size = qr_img.size[0]

            # --- Card dimensions ---
            card_width = qr_size + 80          # padding left/right
            header_height = 70                 # tenant name area
            footer_height = 110                # customer name + PIN area
            border = 8                         # golden border thickness
            card_height = header_height + qr_size + footer_height + 40

            # --- Create white card ---
            card = Image.new('RGBA', (card_width, card_height), (255, 255, 255, 255))
            draw = ImageDraw.Draw(card)

            # --- Golden border ---
            gold = (184, 134, 11)
            light_gold = (255, 215, 0)

            # outer border
            draw.rectangle(
                [0, 0, card_width - 1, card_height - 1],
                outline=gold, width=border
            )
            # inner border (double line effect)
            draw.rectangle(
                [border + 4, border + 4, card_width - border - 5, card_height - border - 5],
                outline=light_gold, width=2
            )

            # --- Try to load a font, fall back to default ---
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
                font_pin_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
                font_pin = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            except Exception:
                font_large = ImageFont.load_default()
                font_medium = font_large
                font_small = font_large
                font_pin_label = font_large
                font_pin = font_large

            # --- Header: tenant name ---
            tenant_name = schema.upper().replace('_', ' ')
            tenant_bbox = draw.textbbox((0, 0), tenant_name, font=font_large)
            tenant_w = tenant_bbox[2] - tenant_bbox[0]
            draw.text(
                ((card_width - tenant_w) // 2, border + 14),
                tenant_name,
                font=font_large,
                fill=gold
            )

            # thin gold divider under header
            draw.line(
                [border + 10, header_height - 8, card_width - border - 10, header_height - 8],
                fill=light_gold, width=1
            )

            # --- Paste QR code onto card ---
            qr_x = (card_width - qr_size) // 2
            qr_y = header_height + 10
            card.paste(qr_img, (qr_x, qr_y), qr_img)

            # thin gold divider above footer
            divider_y = qr_y + qr_size + 10
            draw.line(
                [border + 10, divider_y, card_width - border - 10, divider_y],
                fill=light_gold, width=1
            )

            # --- Footer: customer name ---
            footer_y = divider_y + 12
            customer_label = "CUSTOMER"
            cl_bbox = draw.textbbox((0, 0), customer_label, font=font_pin_label)
            cl_w = cl_bbox[2] - cl_bbox[0]
            draw.text(
                ((card_width - cl_w) // 2, footer_y),
                customer_label,
                font=font_pin_label,
                fill=(150, 150, 150)
            )

            customer_name = self.name.upper()
            cn_bbox = draw.textbbox((0, 0), customer_name, font=font_medium)
            cn_w = cn_bbox[2] - cn_bbox[0]
            draw.text(
                ((card_width - cn_w) // 2, footer_y + 16),
                customer_name,
                font=font_medium,
                fill=(40, 40, 40)
            )

            # --- Footer: access PIN ---
            pin_label = "ACCESS PIN"
            pl_bbox = draw.textbbox((0, 0), pin_label, font=font_pin_label)
            pl_w = pl_bbox[2] - pl_bbox[0]
            draw.text(
                ((card_width - pl_w) // 2, footer_y + 44),
                pin_label,
                font=font_pin_label,
                fill=(150, 150, 150)
            )

            pin_text = str(self.access_pin)
            # draw each digit with spacing for clarity
            spaced_pin = '  '.join(pin_text)
            sp_bbox = draw.textbbox((0, 0), spaced_pin, font=font_pin)
            sp_w = sp_bbox[2] - sp_bbox[0]
            draw.text(
                ((card_width - sp_w) // 2, footer_y + 60),
                spaced_pin,
                font=font_pin,
                fill=gold
            )

            # --- customer code small text at very bottom ---
            code_text = self.customer_code
            cc_bbox = draw.textbbox((0, 0), code_text, font=font_pin_label)
            cc_w = cc_bbox[2] - cc_bbox[0]
            draw.text(
                ((card_width - cc_w) // 2, card_height - border - 22),
                code_text,
                font=font_pin_label,
                fill=(180, 180, 180)
            )

            # --- Save to storage ---
            final_buffer = BytesIO()
            card.convert('RGB').save(final_buffer, format='PNG', optimize=True)
            final_buffer.seek(0)

            filename = f"qr_{self.customer_code}.png"
            self.qr_code.save(filename, ContentFile(final_buffer.getvalue()), save=False)
            Customer.objects.filter(pk=self.pk).update(qr_code=self.qr_code.name)

        except Exception as e:
            import traceback
            print(f"QR generation failed: {e}")
            traceback.print_exc()


class Invoice(models.Model):    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    customer_name = models.CharField(max_length=100)  # kept for backward compatibility, see note below
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(max_length=250)

    def __str__(self):
        return f"Invoice #{self.id} — {self.customer.name}"