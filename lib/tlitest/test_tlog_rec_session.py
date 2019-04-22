""" tlog tests """
import os
import stat
import time
import inspect
from tempfile import mkdtemp

from misc import check_recording, mklogfile, mkcfgfile, \
                 ssh_pexpect, check_recording_missing, copyfile


class TestTlogRecSession:
    """ Test tlog-rec-session functionality """
    user = 'tlitestlocaluser2'
    tempdir = mkdtemp(prefix='/tmp/TestRecSession.')
    os.chmod(tempdir, stat.S_IRWXU + stat.S_IRWXG + stat.S_IRWXO +
             stat.S_ISUID + stat.S_ISGID + stat.S_ISVTX)

    def test_session_record_to_file(self):
        """
        Check tlog-rec-session preserves session in a file
        """
        myname = inspect.stack()[0][3]
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        shell.sendline('echo {}'.format(myname))
        shell.sendline('exit')
        check_recording(shell, myname, logfile)
        shell.close()

    def test_session_record_to_journal(self):
        """
        Check tlog-rec-session preserves session in journal
        """
        myname = inspect.stack()[0][3]
        cfg = '''
        {
            "writer": "journal",
        }
        '''
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        shell.sendline('echo {}'.format(myname))
        shell.sendline('exit')
        check_recording(shell, myname)
        shell.close()

    def test_session_record_to_syslog(self):
        """
        Check tlog-rec-session preserves session via syslog
        """
        myname = inspect.stack()[0][3]
        cfg = '''
        {
            "writer": "syslog",
        }
        '''
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        shell.sendline('echo {}'.format(myname))
        shell.sendline('exit')
        check_recording(shell, myname)
        shell.close()

    def test_session_record_fast_input_with_latency(self):
        """
        Check tlog-rec-session caches data some time before logging
        """
        myname = inspect.stack()[0][3]
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
            "latency": 15,
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        for num in range(0, 200):
            shell.sendline('echo {}_{}'.format(myname, num))
        shell.sendline('exit')
        check_recording(shell, '{}_199'.format(myname), logfile)
        shell.close()

    def test_session_record_fast_input_with_payload(self):
        """
        Check tlog-rec limits output payload size
        """
        myname = inspect.stack()[0][3]
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
            "payload": 128,
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        for num in range(0, 200):
            shell.sendline('echo {}_{}'.format(myname, num))
        shell.sendline('exit')
        check_recording(shell, '{}_199'.format(myname), logfile)
        shell.close()

    def test_session_record_fast_input_with_limit_rate(self):
        """
        Check tlog-rec-session records session with limit rate
        configured
        """
        myname = inspect.stack()[0][3]
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
            "limit": {{
                "rate": 10,
            }},
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        for num in range(0, 200):
            shell.sendline('echo {}_{}'.format(myname, num))
        shell.sendline('exit')
        check_recording(shell, '{}_199'.format(myname), logfile)
        shell.close()

    def test_session_record_fast_input_with_limit_burst(self):
        """
        Check tlog-rec-session allows limited burst of fast output
        """
        myname = inspect.stack()[0][3]
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
            "limit": {{
                "rate": 10,
                "burst": 100,
            }},
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        for num in range(0, 200):
            shell.sendline('echo {}_{}'.format(myname, num))
        shell.sendline('exit')
        check_recording(shell, '{}_199'.format(myname), logfile)
        shell.close()

    def test_session_record_fast_input_with_limit_action_drop(self):
        """
        Check tlog-rec-session drops output when logging limit reached
        """
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
            "limit": {{
                "rate": 10,
                "action": "drop",
            }},
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        shell.sendline('cat /usr/share/dict/linux.words')
        time.sleep(1)
        shell.sendline('exit')
        shell.close()
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        check_recording_missing(shell, 'Byronite', logfile)
        check_recording_missing(shell, 'zygote', logfile)

    def test_session_record_fast_input_with_limit_action_delay(self):
        """
        Check tlog-rec-session delays recording when logging limit reached
        """
        myname = inspect.stack()[0][3]
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
            "limit": {{
                "rate": 500,
                "action": "delay",
            }},
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        for num in range(0, 200):
            shell.sendline('echo {}_{}'.format(myname, num))
        shell.sendline('exit')
        check_recording(shell, '{}_199'.format(myname), logfile)
        shell.close()

    def test_session_record_fast_input_with_limit_action_pass(self):
        """
        Check tlog-rec-session ignores logging limits
        """
        myname = inspect.stack()[0][3]
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
            "limit": {{
                "rate": 500,
                "action": "pass",
            }},
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        for num in range(0, 200):
            shell.sendline('echo {}_{}'.format(myname, num))
        shell.sendline('exit')
        check_recording(shell, '{}_199'.format(myname), logfile)
        shell.close()

    def test_session_record_with_different_shell(self):
        """
        Check tlog-rec-session can specify different shell
        """
        logfile = mklogfile(self.tempdir)
        cfg = '''
        {{
            "shell": "/usr/bin/tcsh",
            "writer": "file",
            "file": {{
                "path": "{}",
            }},
        }}
        '''.format(logfile)
        mkcfgfile('/etc/tlog/tlog-rec-session.conf', cfg)
        shell = ssh_pexpect(self.user, 'Secret123', 'localhost')
        shell.sendline('echo $SHELL')
        check_recording(shell, '/usr/bin/tcsh', logfile)
        shell.sendline('exit')

    @classmethod
    def teardown_class(cls):
        """ Copy original conf file back into place """
        filename = '/etc/tlog/tlog-rec-session.conf'
        bkup = '{}.origtest'.format(filename)
        copyfile(bkup, filename)
