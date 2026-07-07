# billing/models.py
from django.db import models
import uuid
import random


class Slot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=100)  # e.g. "Morning Session", "Table 3"
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    booked_by = models.OneToOneField(
        'Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booked_slot'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    @property
    def is_available(self):
        return self.status == 'available' and self.booked_by is None

    def __str__(self):
        return f"{self.title} | {self.date} {self.start_time}–{self.end_time} | {self.status}"


class Customer(models.Model):
    customer_code = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    access_pin = models.CharField(max_length=6, unique=True, editable=False, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    qr_code = models.ImageField(upload_to='customer_qr/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = self.generate_customer_code()
        if not self.access_pin:
            self.access_pin = self.generate_access_pin()
        super().save(*args, **kwargs)
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
            url = f"http://{schema}.localhost:8000/verify/?c={self.customer_code}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                back_color=(255, 255, 255),
                fill_color=(184, 134, 11),
            ).convert('RGBA')

            qr_size = qr_img.size[0]
            card_width = qr_size + 80
            header_height = 70
            footer_height = 110
            border = 8
            card_height = header_height + qr_size + footer_height + 40

            card = Image.new('RGBA', (card_width, card_height), (255, 255, 255, 255))
            draw = ImageDraw.Draw(card)

            gold = (184, 134, 11)
            light_gold = (255, 215, 0)

            draw.rectangle([0, 0, card_width - 1, card_height - 1], outline=gold, width=border)
            draw.rectangle([border + 4, border + 4, card_width - border - 5, card_height - border - 5], outline=light_gold, width=2)

            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
                font_pin_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
                font_pin = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            except Exception:
                font_large = font_medium = font_pin_label = font_pin = ImageFont.load_default()

            tenant_name = schema.upper().replace('_', ' ')
            tenant_bbox = draw.textbbox((0, 0), tenant_name, font=font_large)
            tenant_w = tenant_bbox[2] - tenant_bbox[0]
            draw.text(((card_width - tenant_w) // 2, border + 14), tenant_name, font=font_large, fill=gold)
            draw.line([border + 10, header_height - 8, card_width - border - 10, header_height - 8], fill=light_gold, width=1)

            card.paste(qr_img, ((card_width - qr_size) // 2, header_height + 10), qr_img)

            divider_y = header_height + qr_size + 20
            draw.line([border + 10, divider_y, card_width - border - 10, divider_y], fill=light_gold, width=1)

            footer_y = divider_y + 12
            customer_name = self.name.upper()
            cn_bbox = draw.textbbox((0, 0), customer_name, font=font_medium)
            draw.text(((card_width - (cn_bbox[2] - cn_bbox[0])) // 2, footer_y + 16), customer_name, font=font_medium, fill=(40, 40, 40))

            pin_label = "ACCESS PIN"
            pl_bbox = draw.textbbox((0, 0), pin_label, font=font_pin_label)
            draw.text(((card_width - (pl_bbox[2] - pl_bbox[0])) // 2, footer_y + 44), pin_label, font=font_pin_label, fill=(150, 150, 150))

            spaced_pin = '  '.join(str(self.access_pin))
            sp_bbox = draw.textbbox((0, 0), spaced_pin, font=font_pin)
            draw.text(((card_width - (sp_bbox[2] - sp_bbox[0])) // 2, footer_y + 60), spaced_pin, font=font_pin, fill=gold)

            cc_bbox = draw.textbbox((0, 0), self.customer_code, font=font_pin_label)
            draw.text(((card_width - (cc_bbox[2] - cc_bbox[0])) // 2, card_height - border - 22), self.customer_code, font=font_pin_label, fill=(180, 180, 180))

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

    def __str__(self):
        return f"{self.customer_code} — {self.name}"


class Invoice(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='invoices'
    )
    slot = models.OneToOneField(
        Slot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} — {self.customer.name}"