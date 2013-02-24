# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Profile'
        db.create_table('cicero_profile', (
            ('user', self.gf('cicero.fields.AutoOneToOneField')(related_name='cicero_profile', unique=True, primary_key=True, to=orm['auth.User'])),
            ('filter', self.gf('django.db.models.fields.CharField')(default='bbcode', max_length=50)),
            ('mutant', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('read_articles', self.gf('cicero.fields.RangesField')()),
            ('moderator', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('cicero', ['Profile'])

        # Adding model 'Forum'
        db.create_table('cicero_forum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('group', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('ordering', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('cicero', ['Forum'])

        # Adding model 'Topic'
        db.create_table('cicero_topic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cicero.Forum'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('deleted', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
            ('spam_status', self.gf('django.db.models.fields.CharField')(default='clean', max_length=20)),
        ))
        db.send_create_signal('cicero', ['Topic'])

        # Adding model 'Article'
        db.create_table('cicero_article', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cicero.Topic'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('filter', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, db_index=True, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cicero.Profile'])),
            ('guest_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('deleted', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
            ('spawned_to', self.gf('django.db.models.fields.related.OneToOneField')(related_name='spawned_from_article', unique=True, null=True, to=orm['cicero.Topic'])),
            ('spam_status', self.gf('django.db.models.fields.CharField')(default='clean', max_length=20)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(default='127.0.0.1', max_length=15)),
            ('votes_up', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('votes_down', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('cicero', ['Article'])

        # Adding model 'Vote'
        db.create_table('cicero_vote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cicero.Profile'])),
            ('article', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cicero.Article'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('cicero', ['Vote'])

        # Adding unique constraint on 'Vote', fields ['profile', 'article']
        db.create_unique('cicero_vote', ['profile_id', 'article_id'])

    def backwards(self, orm):
        # Removing unique constraint on 'Vote', fields ['profile', 'article']
        db.delete_unique('cicero_vote', ['profile_id', 'article_id'])

        # Deleting model 'Profile'
        db.delete_table('cicero_profile')

        # Deleting model 'Forum'
        db.delete_table('cicero_forum')

        # Deleting model 'Topic'
        db.delete_table('cicero_topic')

        # Deleting model 'Article'
        db.delete_table('cicero_article')

        # Deleting model 'Vote'
        db.delete_table('cicero_vote')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 12, 13, 18, 57, 30, 66011)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 12, 13, 18, 57, 30, 65885)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cicero.article': {
            'Meta': {'ordering': "['created']", 'object_name': 'Article'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cicero.Profile']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'deleted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'filter': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'guest_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'default': "'127.0.0.1'", 'max_length': '15'}),
            'spam_status': ('django.db.models.fields.CharField', [], {'default': "'clean'", 'max_length': '20'}),
            'spawned_to': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'spawned_from_article'", 'unique': 'True', 'null': 'True', 'to': "orm['cicero.Topic']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cicero.Topic']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'voters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'voted_articles'", 'symmetrical': 'False', 'through': "orm['cicero.Vote']", 'to': "orm['cicero.Profile']"}),
            'votes_down': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'votes_up': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'cicero.forum': {
            'Meta': {'ordering': "['ordering', 'group']", 'object_name': 'Forum'},
            'group': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ordering': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'cicero.profile': {
            'Meta': {'object_name': 'Profile'},
            'filter': ('django.db.models.fields.CharField', [], {'default': "'bbcode'", 'max_length': '50'}),
            'moderator': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mutant': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'read_articles': ('cicero.fields.RangesField', [], {}),
            'user': ('cicero.fields.AutoOneToOneField', [], {'related_name': "'cicero_profile'", 'unique': 'True', 'primary_key': 'True', 'to': "orm['auth.User']"})
        },
        'cicero.topic': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Topic'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'deleted': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cicero.Forum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'spam_status': ('django.db.models.fields.CharField', [], {'default': "'clean'", 'max_length': '20'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'cicero.vote': {
            'Meta': {'unique_together': "[('profile', 'article')]", 'object_name': 'Vote'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cicero.Article']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cicero.Profile']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['cicero']