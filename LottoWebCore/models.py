from django.contrib.auth.models import User
from django.db import models
from django.db.models import ManyToManyField, DateTimeField, ForeignKey, OneToOneField, Model
from django.db.models.signals import post_save
from django.dispatch import receiver

from LottoWebCore.methods import create_hash


class JSONModel(models.Model):
    def __repr__(self):
        return str(self.to_dict)

    def to_dict(self):
        opts = self._meta
        #
        data = {}
        #
        for f in opts.concrete_fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if self.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(self).values_list('pk', flat=True))
            elif isinstance(f, DateTimeField):
                if f.value_from_object(self) is not None:
                    data[f.name] = f.value_from_object(self).timestamp()
                else:
                    data[f.name] = None
            # elif isinstance(f, ForeignKey):
            #     print(f.value_from_object(self))
            else:
                data[f.name] = f.value_from_object(self)
        return data

    class Meta:
        abstract = True


class City(models.Model):
    name = models.CharField(max_length=500, verbose_name='Cidade', unique=True, null=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"


class University(models.Model):
    name = models.CharField(max_length=500, verbose_name='Universidade', unique=True)
    page = models.CharField(max_length=500, verbose_name='Website')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Universidade"
        verbose_name_plural = "Universidades"


class StudentDirectory(models.Model):
    name = models.CharField(max_length=500, null=False, verbose_name='Nome do Centro')
    acronym = models.CharField(max_length=12, null=False, verbose_name='Sigla do Centro')
    phone = models.CharField(max_length=500, null=False, verbose_name='Telefone ou Ramal')
    email = models.CharField(max_length=500, null=False, verbose_name='E-mail')
    room = models.CharField(max_length=500, verbose_name='Sala')
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=False, verbose_name='Cidade')
    id = models.CharField(max_length=500, default=create_hash, unique=True, primary_key=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, null=False, verbose_name='Universidade')

    class Meta:
        unique_together = ("name", "university", "city")
        verbose_name = "Centro Acadêmico"
        verbose_name_plural = "Centros Acadêmicos"

    def __str__(self):
        return self.name if not self.acronym else self.acronym


class Prize(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=500, verbose_name='Descrição da Premiação')
    qtde = models.IntegerField(verbose_name='Multiplicidade da Premiação', null=False, default=1)

    class Meta:
        verbose_name = "Prêmio"
        verbose_name_plural = "Prêmios"


class Raffle(models.Model):
    name = models.CharField(max_length=500, verbose_name='Nome da Rifa')
    phone = models.CharField(max_length=500, verbose_name='Telefone do Responsável')
    email = models.CharField(max_length=500, verbose_name='E-mail')
    prizes = models.ManyToManyField(Prize, default=None)
    completed = models.BooleanField(default=False, verbose_name="Finalizado")
    creation = models.DateField(auto_now_add=True)
    lottery = models.DateField(null=True, verbose_name="Data do Sorteio")
    id = models.CharField(max_length=500, default=create_hash, unique=True, primary_key=True)
    directory = models.ForeignKey(StudentDirectory, on_delete=models.CASCADE, verbose_name='Centro Acadêmico')

    readonly_fields = ('id',)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Rifa"
        verbose_name_plural = "Rifas"


class MiddleMan(JSONModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='profile')
    phone = models.CharField(max_length=500, null=True)
    picture = models.CharField(max_length=500, null=True)
    raffle = models.ForeignKey(Raffle, null=True, on_delete=models.CASCADE)
    directory = models.ForeignKey(StudentDirectory, null=True, on_delete=models.CASCADE)
    id = models.CharField(max_length=500, default=create_hash, unique=True, primary_key=True)

    readonly_fields = ('id',)

    class Meta:
        # unique_together = ["user", "directory"]#, "raffle"]
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"

    def __str__(self):
        return self.full_name

    @property
    def centro(self):
        return self.directory.name

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def name(self):
        return self.full_name

    @property
    def email(self):
        return self.user.email

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def full_name(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        MiddleMan.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    print(instance)
    # instance.profile.save()


class Ticket(JSONModel):
    name = models.CharField(max_length=500, verbose_name='Comprador', null=True)
    phone = models.CharField(max_length=500, verbose_name='Telefone', null=True)
    email = models.CharField(max_length=500, verbose_name='E-mail', null=True)
    notified = models.BooleanField(default=False)  # by the SERVER and to the client
    activated = models.BooleanField(default=False)  # by LABAM
    winner = models.BooleanField(default=False)  # by LABAM
    flagged = models.BooleanField(default=False)  # by USER if NOT activated
    created = models.DateTimeField(auto_now_add=True)
    seller = models.ForeignKey(MiddleMan, on_delete=models.CASCADE, verbose_name='Vendedor')
    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, verbose_name='Rifa')
    id = models.CharField(max_length=500, default=create_hash, unique=True, primary_key=True, verbose_name='Ticket ID')
    directory = models.ForeignKey(StudentDirectory, on_delete=models.CASCADE, verbose_name='Centro Acadêmico')

    readonly_fields = ('id',)

    def __str__(self):
        return self.id

    class Meta:
        verbose_name = "Bilhete"
        verbose_name_plural = "Bilhetes"


#
# class RegistrationRequest(models.Model):
#     name = models.CharField(max_length=500, null=False, verbose_name="Nome")
#     email = models.CharField(max_length=500, null=False, unique=True, verbose_name="E-mail")
#     message = models.TextField(blank=True, verbose_name="Informações Adicionais")
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name = "Solicitação de Registro"
#         verbose_name_plural = "Solicitações de Registro"

class RegistrationRequest(models.Model):
    name = models.CharField(max_length=500, null=False, verbose_name="Nome Completo")
    username = models.CharField(max_length=12, null=True, verbose_name="Nome de Usuário")
    phone = models.CharField(max_length=500, null=False, verbose_name="Telefone")
    email = models.CharField(max_length=500, null=False, unique=True, verbose_name="E-mail")
    social_media = models.CharField(max_length=500, null=True, verbose_name="Facebook/Instagram (URL)")
    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, verbose_name="Rifa")
    directory = models.ForeignKey(StudentDirectory, on_delete=models.CASCADE, verbose_name="Centro Acadêmico")
    analysed = models.BooleanField(default=False)

    class Meta:
        unique_together = ["name", "directory", "raffle", "email"]
        verbose_name = "Solicitação de Registro"
        verbose_name_plural = "Solicitações de Registro"

    def __str__(self):
        return self.name
