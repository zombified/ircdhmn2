# http://twistedmatrix.com/documents/10.2.0/core/howto/clients.html

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
import re


class IRCDHMN(irc.IRCClient):
    nickname = "ircdhmn"

    def _outbound_say(self, msg, user=""):
        if self.factory.outbound == None: 
            return

        if self.factory.outbound_prefix == None: 
            self.factory.outbound_prefix = ""
        
        if user == None: 
            user = ""
        else:
            # just grab the nick portion of the user that we saw the message from
            user = "%s> " % self._parse_nick(user)

        finalmsg = "%s%s%s" % (self.factory.outbound_prefix, user, msg)
        self.factory.outbound.say(self.factory.outbound_channel, finalmsg, irc.MAX_COMMAND_LENGTH)

    def _self_say(self, msg, user=""):
        if user == None: 
            user = ""
        else:
            # just grab the nick portion of the user that we saw the message from
            user = "%s: " % self._parse_nick(user)

        finalmsg = "%s%s" % (user, msg)

        self.say(self.factory.channel, finalmsg, irc.MAX_COMMAND_LENGTH)

    def _parse_nick(self, user):
        re_user = re.compile(r'^(.*)!.*$')
        m = re_user.match(user)
        if m == None:
            return user
        else:
            return m.group(1)


    def signedOn(self):
        self.join(self.factory.channel)

    def joined(self, channel):
        self.factory.regdhmn(self, self.factory.channel)


    def alterCollidedNick(self, nickname):
        return nickname + "^"

    
    def userJoined(self, user, channel):
        if user == self.nickname: return
        self._outbound_say("%s joined the channel" % self._parse_nick(user))
    
    def userLeft(self, user, channel):
        if user == self.nickname: return
        self._outbound_say("%s left the channel" % self._parse_nick(user))
    
    def userQuit(self, user, quitMessage):
        if user == self.nickname: return
        self._outbound_say("%s has quit [%s]" % (self._parse_nick(user), quitMessage))

    def userKicked(self, kickee, channel, kicker, message):
        self._outbound_say("%s kicked by %s [%s]" % (self._parse_nick(kickee), self._parse_nick(kicker), message))

    def userRenamed(self, oldname, newname):
        self._outbound_say("%s is now known as %s" % (self._parse_nick(oldname), self._parse_nick(newname)))

    def action(self, user, channel, data):
        self._outbound_say("*%s %s" % (self._parse_nick(user), data))

    #def topicUpdated(self, user, channel, newTopic):
    #    self._outbound_say("The channel topic was changed to '%s' by %s" % (user, newTopic))

                                                
    def privmsg(self, user, channel, msg):
        # now, do commands if the
        re_iscmd = re.compile('^%s: ?(.*)$' % self.nickname, re.IGNORECASE)
        cmd_match = re_iscmd.match(msg)
        if cmd_match == None:
            self._outbound_say(msg, user)
            return
        
        # if a command was given, see which command was given
        re_cmd_name = re.compile('^name$', re.IGNORECASE)
        cmd_match = re_cmd_name.match(cmd_match.group(1).strip())
        if cmd_match != None:
            self.name()


    def name(self):
        self.factory.outbound.sendLine('NAMES %s' % self.factory.channel)

    def lineReceived(self, line):
        irc.IRCClient.lineReceived(self, line)
        print line

    def irc_RPL_NAMREPLY(self, *nargs):
        try:
            if self.factory.gotInitialNames :
                self._outbound_say(nargs[1][3])

            self.factory.gotInitialNames = True
        except:
            print 'error'

    def irc_RPL_ENDOFNAMES(self, *nargs):
        pass
        #print "END OF NAMES"

    def irc_unknown(self, prefix, command, params):
        pass
        #print 'UNKNOWN: ', prefix, command, params

    
        
    


class IRCDHMN_Factory(protocol.ClientFactory):
    protocol = IRCDHMN

    def __init__(self, channel, prefix):
        self.channel = channel
        self.regdhmn = None
        self.outbound = None
        self.outbound_channel = None
        self.outbound_prefix = prefix
        self.gotInitialNames = False


    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


    def set_outbound(self, dhmn, channel):
        self.outbound = dhmn
        self.outbound_channel = channel
        


if __name__ == "__main__":
    freenode = IRCDHMN_Factory("#dhmn", "(fn) ")
    espernet = IRCDHMN_Factory("#dhmn", "(en) ")

    freenode.regdhmn = espernet.set_outbound
    espernet.regdhmn = freenode.set_outbound

    reactor.connectTCP("irc.freenode.net", 6667, freenode)
    reactor.connectTCP("irc.esper.net", 6667, espernet)

    reactor.run()


