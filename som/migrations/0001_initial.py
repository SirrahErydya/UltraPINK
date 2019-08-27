# Generated by Django 2.2.3 on 2019-08-26 11:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Prototype',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proto_id', models.IntegerField(unique=True)),
                ('image', models.ImageField(upload_to='prototypes')),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('z', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='SOM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('som_path', models.FileField(upload_to='bin')),
                ('mapping_path', models.FileField(upload_to='bin')),
                ('data_path', models.FileField(upload_to='bin')),
                ('csv_path', models.FileField(upload_to='data')),
                ('n_cutouts', models.IntegerField()),
                ('n_outliers', models.IntegerField()),
                ('training_dataset_name', models.CharField(max_length=200)),
                ('number_of_images', models.IntegerField()),
                ('number_of_channels', models.IntegerField()),
                ('som_width', models.DecimalField(decimal_places=15, max_digits=20)),
                ('som_height', models.DecimalField(decimal_places=15, max_digits=20)),
                ('som_depth', models.DecimalField(decimal_places=15, max_digits=20)),
                ('layout', models.CharField(max_length=200)),
                ('som_label', models.CharField(max_length=200)),
                ('rotated_size', models.DecimalField(decimal_places=15, max_digits=20)),
                ('full_size', models.IntegerField()),
                ('gauss_start', models.DecimalField(decimal_places=15, max_digits=20)),
                ('learning_constraint', models.DecimalField(decimal_places=15, max_digits=20)),
                ('epochs_per_epoch', models.DecimalField(decimal_places=15, max_digits=20)),
                ('gauss_decrease', models.DecimalField(decimal_places=15, max_digits=20)),
                ('gauss_end', models.DecimalField(decimal_places=15, max_digits=20)),
                ('pbc', models.CharField(max_length=200)),
                ('learning_constraint_decrease', models.DecimalField(decimal_places=15, max_digits=20)),
                ('random_seed', models.DecimalField(decimal_places=15, max_digits=20)),
                ('init', models.CharField(max_length=200)),
                ('pix_angular_res', models.DecimalField(decimal_places=15, max_digits=20)),
                ('rotated_size_arcsec', models.DecimalField(decimal_places=15, max_digits=20)),
                ('full_size_arcsec', models.DecimalField(decimal_places=15, max_digits=20)),
            ],
        ),
        migrations.CreateModel(
            name='SomCutout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ra', models.DecimalField(decimal_places=15, max_digits=20)),
                ('dec', models.DecimalField(decimal_places=15, max_digits=20)),
                ('csv_path', models.FilePathField()),
                ('csv_row_idx', models.IntegerField()),
                ('image', models.ImageField(upload_to='cutouts')),
                ('closest_prototype', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='som.Prototype')),
                ('som', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='som.SOM')),
            ],
        ),
        migrations.AddField(
            model_name='prototype',
            name='som',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='som.SOM'),
        ),
        migrations.CreateModel(
            name='Outlier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ra', models.DecimalField(decimal_places=15, max_digits=20)),
                ('dec', models.DecimalField(decimal_places=15, max_digits=20)),
                ('csv_path', models.FilePathField()),
                ('csv_row_idx', models.IntegerField()),
                ('image', models.ImageField(upload_to='outliers')),
                ('som', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='som.SOM')),
            ],
        ),
        migrations.CreateModel(
            name='Distance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance', models.DecimalField(decimal_places=15, max_digits=20)),
                ('cutout', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='som.SomCutout')),
                ('prototype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='som.Prototype')),
            ],
        ),
    ]