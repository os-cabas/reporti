class Dispositivo(models.Model):
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True)
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.modelo} - {self.sala}'