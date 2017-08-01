from heltour import settings
from heltour.tournament.models import *
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from heltour.tournament.tasks import pairings_published
import reversion

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ModRequest, dispatch_uid='heltour.tournament.automod')
def mod_request_saved(instance, created, **kwargs):
    if created:
        signals.mod_request_created.send(sender=MOD_REQUEST_SENDER[instance.type], instance=instance)

@receiver(signals.mod_request_created, sender=MOD_REQUEST_SENDER['appeal_late_response'], dispatch_uid='heltour.tournament.automod')
def appeal_late_response_created(instance, **kwargs):
    pass

@receiver(signals.mod_request_created, sender=MOD_REQUEST_SENDER['withdraw'], dispatch_uid='heltour.tournament.automod')
def withdraw_created(instance, **kwargs):
    # Figure out which round to add the withdrawal on
    if not instance.round or instance.round.publish_pairings:
        instance.round = instance.season.round_set.order_by('number').filter(publish_pairings=False).first()
        instance.save()

    # Check that the requester is part of the season
    sp = SeasonPlayer.objects.filter(player=instance.requester, season=instance.season).first()
    if sp is None:
        instance.reject(response='You aren\'t currently a participant in %s.' % instance.season)
        return

    if not instance.round:
        instance.reject(response='You can\'t withdraw from the season at this time.')
        return

    instance.approve(response='You\'ve been withdrawn for round %d.' % instance.round.number)

@receiver(signals.mod_request_approved, sender=MOD_REQUEST_SENDER['withdraw'], dispatch_uid='heltour.tournament.automod')
def withdraw_approved(instance, **kwargs):
    # Add the withdrawal if it doesn't already exist
    with reversion.create_revision():
        reversion.set_comment('Withdraw request approved by %s' % instance.status_changed_by)
        PlayerWithdrawal.objects.get_or_create(player=instance.requester, round=instance.round)

@receiver(signals.automod_unresponsive, dispatch_uid='heltour.tournament.automod')
def automod_unresponsive(round_, **kwargs):
    for p in round_.pairings.filter(game_link='', result='', scheduled_time=None).exclude(white=None).exclude(black=None):
        white_present = p.get_player_presence(p.white).first_msg_time is not None
        black_present = p.get_player_presence(p.black).first_msg_time is not None
        if not white_present:
            player_unresponsive(round_, p, p.white)
            if black_present:
                signals.notify_opponent_unresponsive.send(sender=automod_unresponsive, round_=round_, player=p.black, opponent=p.white)
        if not black_present:
            player_unresponsive(round_, p, p.black)
            if white_present:
                signals.notify_opponent_unresponsive.send(sender=automod_unresponsive, round_=round_, player=p.white, opponent=p.black)

def player_unresponsive(round_, pairing, player):
    has_warning = PlayerWarning.objects.filter(player=player, round__season=round_.season).exists()
    if not has_warning:
        with reversion.create_revision():
            reversion.set_comment('Automatic warning for unresponsiveness')
            PlayerWarning.objects.create(player=player, round=round_, type='unresponsive')
        punishment = 'You may receive a yellow card.'
        allow_continue = True
    else:
        sp = SeasonPlayer.objects.filter(season=round_.season, player=player).first()
        if not sp:
            logger.error('Season player did not exist for %s %s' % (round_.season, player))
            return
        sp.games_missed += 1
        if sp.games_missed < 2:
            punishment = 'You have been given a yellow card.'
            allow_continue = True
            with reversion.create_revision():
                reversion.set_comment('Automatic yellow card for unresponsiveness')
                sp.save()
        else:
            punishment = 'You have been given a red card.'
            allow_continue = False
            with reversion.create_revision():
                reversion.set_comment('Automatic red card for unresponsiveness')
                sp.save()
    signals.notify_unresponsive.send(sender=automod_unresponsive, round_=round_, player=player, punishment=punishment, allow_continue=allow_continue)
