from django.core.management.base import BaseCommand
from django.utils import timezone
from fondiart_api.models import User, ArtistPerformance, Artwork
from finance.models import Transaccion
from django.db.models import Sum, Avg, Count

class Command(BaseCommand):
    help = 'Updates artist performance data for K-Means clustering.'

    def handle(self, *args, **options):
        self.stdout.write('Starting artist performance update...')
        
        today = timezone.now().date()
        ArtistPerformance.objects.all().delete()
        self.stdout.write(f'Cleared all old performance data.')

        artists = User.objects.filter(role='artist')
        performance_data = []

        for artist in artists:
            artworks = Artwork.objects.filter(artist=artist)
            
            sales = Transaccion.objects.filter(
                artwork__in=artworks,
                tipo=Transaccion.TipoTransaccion.COMPRA
            )

            total_sales_revenue = sales.aggregate(Sum('monto_pesos'))['monto_pesos__sum'] or 0
            total_sales_volume = sales.aggregate(Sum('cantidad_tokens'))['cantidad_tokens__sum'] or 0
            number_of_artworks_sold = sales.values('artwork').distinct().count()
            
            average_sale_price = 0
            if total_sales_volume and total_sales_volume > 0:
                average_sale_price = total_sales_revenue / total_sales_volume

            performance = ArtistPerformance.objects.create(
                artist=artist,
                date=today,
                total_sales_volume=total_sales_volume or 0,
                total_sales_revenue=total_sales_revenue or 0,
                average_sale_price=average_sale_price or 0,
                number_of_artworks_sold=number_of_artworks_sold or 0
            )
            performance_data.append(performance)

        self.stdout.write(f'Generated performance data for {len(performance_data)} artists.')

        # K-Means Clustering
        if len(performance_data) >= 3:
            try:
                from sklearn.preprocessing import StandardScaler
                from sklearn.cluster import KMeans
                import pandas as pd

                data_for_clustering = [
                    [p.total_sales_volume, p.total_sales_revenue, p.average_sale_price, p.number_of_artworks_sold]
                    for p in performance_data
                ]

                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(data_for_clustering)

                kmeans = KMeans(n_clusters=3, random_state=0, n_init=10)
                clusters = kmeans.fit_predict(scaled_data)

                for i, performance in enumerate(performance_data):
                    performance.cluster = clusters[i]
                    performance.save()
                
                self.stdout.write('Successfully clustered artists into 3 groups.')

            except ImportError:
                self.stdout.write(self.style.WARNING('scikit-learn is not installed. Skipping clustering. Please run "pip install scikit-learn pandas".'))
        
        self.stdout.write(self.style.SUCCESS('Artist performance update finished.'))
