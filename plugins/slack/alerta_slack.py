import os
import json
import requests
import logging

from alerta.app import app
from alerta.plugins import PluginBase


def convert(value, newtype, default=None):
    try:
        return newtype(value)
    except (TypeError, ValueError):
        return default


LOG = logging.getLogger('alerta.plugins.slack')

SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL') or app.config['SLACK_WEBHOOK_URL']
SLACK_ATTACHMENTS = True if os.environ.get('SLACK_ATTACHMENTS', 'False') == 'True' else app.config.get('SLACK_ATTACHMENTS', False)
SLACK_USERNAME = os.environ.get('SLACK_USERNAME') or app.config.get('SLACK_USERNAME')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL') or app.config.get('SLACK_CHANNEL')
SLACK_ICON_EMOJI = os.environ.get('SLACK_ICON_EMOJI') or app.config.get('SLACK_ICON_EMOJI')
SLACK_TIMEOUT = convert(os.environ.get('SLACK_TIMEOUT'), int) or app.config.get('SLACK_TIMEOUT') or 2
SLACK_SEVERITY_IGNORED = (os.environ.get('SLACK_SEVERITY_IGNORED') or ','.join(app.config.get('SLACK_SEVERITY_IGNORED', ['indeterminate']))).split(',')
ALERTA_UI_URL = os.environ.get('ALERTA_UI_URL') or app.config.get('ALERTA_UI_URL', 'http://localhost')


class ServiceIntegration(PluginBase):
    def _send_to_slack(self, alert, changed_status=None, changed_text=None):
        if changed_status is not None and changed_status not in ['ack', 'closed', 'open']:
            return

        if alert.severity in SLACK_SEVERITY_IGNORED:
            return

        if alert.previous_severity in SLACK_SEVERITY_IGNORED and alert.severity == 'normal':
            return

        if changed_status is None and alert.repeat:
            return

        url = SLACK_WEBHOOK_URL

        if changed_status in ['ack', 'closed']:
            color = "#00CC00"  # green
        elif alert.severity == 'critical':
            color = "#FF0000"  # red
        elif alert.severity == 'major':
            color = "#FFA500"  # orange
        elif alert.severity == 'minor':
            color = "#FFFF00"  # yellow
        elif alert.severity == 'warning':
            color = "#1E90FF"  # blue
        else:
            color = "#00CC00"  # green

        status = changed_status or alert.status

        summary = "*[%s] %s %s - _%s on %s_* <%s/#/alert/%s|%s>" % (
            status.capitalize(), alert.environment, alert.severity.capitalize(), alert.event, alert.resource, ALERTA_UI_URL,
            alert.id, alert.get_id(short=True)
        )

        text = "<%s/#/alert/%s|%s> %s - %s" % (ALERTA_UI_URL, alert.get_id(), alert.get_id(short=True), alert.event, alert.text)

        if changed_text is not None:
            summary += " - %s" % (changed_text)
            text += " - %s" % (changed_text)

        if not SLACK_ATTACHMENTS:

            payload = {
                "text": summary,
            }

        else:
            payload = {
                "attachments": [{
                    "fallback": summary,
                    "color": color,
                    "pretext": text,
                    "fields": [
                        {"title": "Status", "value": status.capitalize(), "short": True},
                        {"title": "Environment", "value": alert.environment, "short": True},
                        {"title": "Resource", "value": alert.resource, "short": True},
                        {"title": "Services", "value": ", ".join(alert.service), "short": True}
                    ]
                }]
            }

        if SLACK_USERNAME:
            payload['username'] = SLACK_USERNAME

        if SLACK_CHANNEL:
            payload['channel'] = SLACK_CHANNEL

        if SLACK_ICON_EMOJI:
            payload['icon_emoji'] = SLACK_ICON_EMOJI

        LOG.debug('Slack payload: %s', payload)

        try:
            r = requests.post(url, data=json.dumps(payload), timeout=SLACK_TIMEOUT)
        except Exception as e:
            raise RuntimeError("Slack connection error: %s", e)

        LOG.debug('Slack response: %s', r.status_code)

    def pre_receive(self, alert):
        return alert

    def post_receive(self, alert):
        self._send_to_slack(alert)

    def status_change(self, alert, status=None, text=None):
        self._send_to_slack(alert, status, text)
