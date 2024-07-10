# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

import logging
import requests

_logger = logging.getLogger(__name__)

SMS_API_SI_CREDIT_BALANCE_URL = 'http://www.smsapi.si/preveri-stanje-kreditov'

class IapAccount(models.Model):
    _name = "iap.account"
    _inherit = ['iap.account', 'mail.thread', 'mail.activity.mixin']

    SMS_API_SI_ERRORS = {
        '1': {'name': _('Validation error.'), 'description': _('Incorrect username or password.')},
        '2': {'name': _('Message error.'), 'description': _('The message is longer than 640 characters or is empty.')},
        '3': {'name': _('Sender number error.'), 'description': _('The sender number is not formed correctly or is empty.')},
        '4': {'name': _('Recipient number error.'), 'description': _('The recipient\'s number is not formed correctly or is empty.')},
        '5': {'name': _('Not enough credits.'), 'description': _('User does not have enough credits.')},
        '6': {'name': _('Server error.'), 'description': _('Error on the SMSapi.si page due to technical problems.')},
        '7': {'name': _('The sender number is not registered.'), 'description': _('If you have purchased your own number so that you can receive replies to it. It may not be valid yet.')},
        '8': {'name': _('The user reference is not valid.'), 'description': _('The reference cannot be longer than 16 characters.')},
        '9': {'name': _('Country code format invalid'), 'description': _('The code must be in the format 00386 or 386')},
        '10': {'name': _('Sender ID not verified.'), 'description': _('SMSapi.si needs to confirm your sender ID')},
        '11': {'name': _('Country code not supported.'), 'description': _('Contact SMSapi.si.')},
        '12': {'name': _('Sender number not confirmed.'), 'description': _('Add the sender\'s number in your profile on the SMSapi.si page and confirm it according to the instructions.')},
    }
    
    provider = fields.Selection(
        selection_add=[("sms_api_si", "smsapi.si")],
        ondelete={"sms_api_si": "cascade"},
    )

    sms_api_username = fields.Char(help="SMSapi.si username")
    sms_api_password = fields.Char(help="SMSapi.si password")
    sms_api_from = fields.Char(help="Sender number or description")
    sms_api_min_tokens = fields.Integer(string="Minimum tokens", help="Minimum credit level for alerting purposes. If it is 0 or a negative number, the alarming is disabled.")
    sms_api_use_sid = fields.Boolean(string="Use SID", help="You want to use your Sender ID that you specified on our website.")
    sms_api_sname = fields.Char(string="Sender ID", help="You can use different IDs. Use sName to specify which one you want to use.")

    @api.model
    def _default_sms_api_token_notification_action(self):
        try:
            default_action = self.env.ref('smsapisi_connector.model_iap_account_action_low_tokens').id
        except ValueError:
            _logger.warning("smsapisi_connector.model_iap_account_action_low_tokens doesn't exist - notification action will have no default.")
            return None
        else:
            return default_action

    sms_api_token_notification_action = fields.Many2one('ir.actions.server', default=_default_sms_api_token_notification_action, string="Token notification action", help="Action to be performed when the number of credits is less than min_tokens.")
    sms_api_si_connection_status = fields.Char(string="Connection status", help="Status of the last connection test.")


    @api.model
    def check_sms_api_si_credit_balance(self):
        """If current credits are lower than sms_api_min_tokens, execute sms_api_token_notification_action"""

        iap_account = self._get_sms_account()

        if iap_account.sms_api_min_tokens < 1:
            _logger.info(f"SMSapi.si minimum tokens not set. Skipping balance check.")
            return

        if not iap_account.sms_api_token_notification_action:
            _logger.info(f"SMSapi.si notification action not set. Skipping balance check.")
            return

        try:
            api_credits = iap_account.get_current_credit_balance()
        except UserWarning as e:
            _logger.warning(f"SMSapi.si returned an error while attempting to get current credit balance: {e}")
        except Exception as e:
            _logger.warning(f"An exception occurred while attempting to get current credit balance: {e}")
        else:
            if api_credits < iap_account.sms_api_min_tokens:
                _logger.info(f"You only have {api_credits} SMSapi.si credits left.")
                ctx = dict(self.env.context or {})
                ctx.update({'active_id': iap_account.id, 'active_model': 'iap.account'})
                iap_account.sms_api_token_notification_action.with_context(ctx).run()
            else:
                _logger.info(f"You have {api_credits} SMSapi.si credits, which is more than your set minimum of {iap_account.sms_api_min_tokens} credits")


    def _prepare_sms_api_si_credit_check_params(self):
        self.ensure_one()

        params = {
            "un": self.sms_api_username,
            "ps": self.sms_api_password,
        }

        return params

    def get_current_credit_balance(self):

        response = requests.get(
            SMS_API_SI_CREDIT_BALANCE_URL,
            params=self._prepare_sms_api_si_credit_check_params(),
        )

        response_content = response.content.decode('utf-8')
        _logger.debug(f"smsapi.si credit balance check responded with: {response_content}")

        if response_content[:2] != "-1":
            current_credit_balance = int(float(response_content))
            return current_credit_balance
        else:
            error_code = response_content.split('##')[1]
            error_msg = self.get_sms_api_si_error(error_code)
            raise UserWarning(error_msg)

    @api.model
    def _get_sms_account(self):
        return self.get("sms")

    @api.model
    def get_sms_api_si_error(self, error_code):
        if error_code not in self.SMS_API_SI_ERRORS:
            return _("smsapi.si returned an unknown error")

        return f"{self.SMS_API_SI_ERRORS[error_code]['name']} {self.SMS_API_SI_ERRORS[error_code]['description']}"

    def sms_api_si_connection_test(self):
        """Test connection by checking current credit balance and writing a status message to sms_api_si_connection_status
        """

        iap_account = self._get_sms_account()
        if iap_account.id != self.id or self.provider != "sms_api_si":
            _logger.warning("SMSapi.si connection test is only performed on SMS account where SMSapi.si is set as provider.")

        try:
            api_credits = iap_account.get_current_credit_balance()
        except UserWarning as e:
            _logger.warning(f"SMSapi.si returned an error while attempting to get current credit balance: {e}")
            iap_account.sms_api_si_connection_status = e
        except Exception as e:
            _logger.warning(f"An exception occurred while attempting to get current credit balance: {e}")
            iap_account.sms_api_si_connection_status = _("Unexpected error. Check server log for more info.")
        else:
            _logger.info("SMSapi.si connection test successful")
            iap_account.sms_api_si_connection_status = "OK"
