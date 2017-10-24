
%global release_version 1

Name: ovirt-guest-agent
Version: 1.0.14
Release: %{release_version}%{?release_suffix}%{?dist}
Summary: The oVirt Guest Agent
Group: Applications/System
License: ASL 2.0
URL: http://wiki.ovirt.org/wiki/Category:Ovirt_guest_agent
Source0: http:///resources.ovirt.org/pub/src/ovirt-guest-agent/%{name}-%{version}.tar.bz2
BuildArch: noarch
BuildRequires: python2-devel
BuildRequires: python-pep8
Requires: dbus-python
Requires: rpm-python
Requires: python-ethtool >= 0.4-1
Requires: udev >= 095-14.23
Requires: kernel > 2.6.18-238.5.0
Requires: usermode
Requires: qemu-guest-agent

Conflicts: rhev-agent
Conflicts: rhevm-guest-agent
Conflicts: rhevm-guest-agent-common
%if 0%{?rhel} <= 6
Conflicts: selinux-policy < 3.7.19-188
%endif

%description
This is the oVirt management agent running inside the guest. The agent
interfaces with the oVirt manager, supplying heart-beat info as well as
run-time data from within the guest itself. The agent also accepts
control commands to be run executed within the OS (like: shutdown and
restart).

%prep
%setup -q -n ovirt-guest-agent-%{version}

%build
%configure \
    --includedir=%{_includedir}/security \
    --without-sso

make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

%if 0%{?rhel}
    # Install SystemV init script.
    install -Dm 0755 ovirt-guest-agent/ovirt-guest-agent %{buildroot}%{_initrddir}/ovirt-guest-agent
%endif

%pre
getent group ovirtagent >/dev/null || groupadd -r -g 175 ovirtagent
getent passwd ovirtagent > /dev/null || \
    /usr/sbin/useradd -u 175 -g 175 -o -r ovirtagent \
    -c "oVirt Guest Agent" -d %{_datadir}/ovirt-guest-agent -s /sbin/nologin
exit 0

%post
/sbin/chkconfig --add ovirt-guest-agent

%posttrans
/sbin/udevadm trigger --subsystem-match="virtio-ports" \
    --attr-match="name=ovirt-guest-agent.0"

/sbin/udevadm trigger --subsystem-match="virtio-ports" \
    --attr-match="name=com.redhat.rhevm.vdsm"

%preun
if [ "$1" -eq 0 ]
then
    /sbin/service ovirt-guest-agent stop > /dev/null 2>&1
    /sbin/chkconfig --del ovirt-guest-agent

    # Send an "uninstalled" notification to vdsm.
    if [ -w /dev/virtio-ports/com.redhat.rhevm.vdsm ]
    then
        # Non blocking uninstalled notification
        echo -e '{"__name__": "uninstalled"}\n' | dd \
            of=/dev/virtio-ports/com.redhat.rhevm.vdsm \
            oflag=nonblock status=noxfer conv=nocreat 1>& /dev/null || :
    fi
    if [ -w /dev/virtio-ports/ovirt-guest-agent.0 ]
    then
        # Non blocking uninstalled notification
        echo -e '{"__name__": "uninstalled"}\n' | dd \
            of=/dev/virtio-ports/ovirt-guest-agent.0 \
            oflag=nonblock status=noxfer conv=nocreat 1>& /dev/null || :
    fi
fi

%postun
if [ "$1" -eq 0 ]
then
    # Let udev clear access rights
    /sbin/udevadm trigger --subsystem-match="virtio-ports" \
        --attr-match="name=com.redhat.rhevm.vdsm"
    /sbin/udevadm trigger --subsystem-match="virtio-ports" \
        --attr-match="name=ovirt-guest-agent.0"

fi

if [ "$1" -ge 1 ]; then
    /sbin/service ovirt-guest-agent condrestart > /dev/null 2>&1
fi

%files
%dir %attr (755,ovirtagent,ovirtagent) %{_localstatedir}/log/ovirt-guest-agent
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent

# Hook configuration directories
%dir %attr (755,root,root) %{_sysconfdir}/ovirt-guest-agent
%dir %attr (755,root,root) %{_sysconfdir}/ovirt-guest-agent/hooks.d
%dir %attr (755,root,root) %{_sysconfdir}/ovirt-guest-agent/hooks.d/before_migration
%dir %attr (755,root,root) %{_sysconfdir}/ovirt-guest-agent/hooks.d/after_migration
%dir %attr (755,root,root) %{_sysconfdir}/ovirt-guest-agent/hooks.d/before_hibernation
%dir %attr (755,root,root) %{_sysconfdir}/ovirt-guest-agent/hooks.d/after_hibernation

# Hook installation directories
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/defaults
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/before_migration
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/after_migration
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/before_hibernation
%dir %attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/after_hibernation
%config(noreplace) %{_sysconfdir}/ovirt-guest-agent.conf

%doc AUTHORS COPYING NEWS README

# These are intentionally NOT 'noreplace' If this is modified by an user,
# this actually might break it.
%config(noreplace) %{_sysconfdir}/pam.d/ovirt-logout
%config(noreplace) %{_sysconfdir}/pam.d/ovirt-locksession
%config(noreplace) %{_sysconfdir}/pam.d/ovirt-shutdown
%config(noreplace) %{_sysconfdir}/pam.d/ovirt-hibernate
%config(noreplace) %{_sysconfdir}/pam.d/ovirt-container-list
%config(noreplace) %{_sysconfdir}/pam.d/ovirt-flush-caches
%config(noreplace) %attr (644,root,root) %{_sysconfdir}/udev/rules.d/55-ovirt-guest-agent.rules
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/org.ovirt.vdsm.Credentials.conf
%config(noreplace) %{_sysconfdir}/security/console.apps/ovirt-logout
%config(noreplace) %{_sysconfdir}/security/console.apps/ovirt-locksession
%config(noreplace) %{_sysconfdir}/security/console.apps/ovirt-shutdown
%config(noreplace) %{_sysconfdir}/security/console.apps/ovirt-hibernate
%config(noreplace) %{_sysconfdir}/security/console.apps/ovirt-container-list
%config(noreplace) %{_sysconfdir}/security/console.apps/ovirt-flush-caches

%attr (755,root,root) %{_datadir}/ovirt-guest-agent/ovirt-guest-agent.py*

%{_datadir}/ovirt-guest-agent/scripts/hooks/defaults/55-flush-caches
%attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/defaults/55-flush-caches.consolehelper
%attr (755,root,root) %{_datadir}/ovirt-guest-agent/scripts/hooks/defaults/flush-caches

%{_datadir}/ovirt-guest-agent/OVirtAgentLogic.py*
%{_datadir}/ovirt-guest-agent/VirtIoChannel.py*
%{_datadir}/ovirt-guest-agent/CredServer.py*
%{_datadir}/ovirt-guest-agent/GuestAgentLinux2.py*
%{_datadir}/ovirt-guest-agent/hooks.py*
%{_datadir}/ovirt-guest-agent/timezone.py*
%{_datadir}/ovirt-guest-agent/ovirt-osinfo
%{_datadir}/ovirt-guest-agent/ovirt-logout

# consolehelper symlinks
%{_datadir}/ovirt-guest-agent/ovirt-locksession
%{_datadir}/ovirt-guest-agent/ovirt-shutdown
%{_datadir}/ovirt-guest-agent/ovirt-hibernate
%{_datadir}/ovirt-guest-agent/ovirt-container-list

# Symlinks for the default hooks
%config(noreplace) %{_datadir}/ovirt-guest-agent/scripts/hooks/before_hibernation/55_flush-caches
%config(noreplace) %{_datadir}/ovirt-guest-agent/scripts/hooks/before_migration/55_flush-caches
%config(noreplace) %{_sysconfdir}/ovirt-guest-agent/hooks.d/before_hibernation/55_flush-caches
%config(noreplace) %{_sysconfdir}/ovirt-guest-agent/hooks.d/before_migration/55_flush-caches

%attr (644,root,root) %{_datadir}/ovirt-guest-agent/default.conf
%attr (644,root,root) %{_datadir}/ovirt-guest-agent/default-logger.conf
%attr (755,root,root) %{_datadir}/ovirt-guest-agent/diskmapper
%attr (755,root,root) %{_datadir}/ovirt-guest-agent/container-list

%attr (755,root,root) %{_datadir}/ovirt-guest-agent/LogoutActiveUser.py*
%attr (755,root,root) %{_datadir}/ovirt-guest-agent/LockActiveSession.py*
%attr (755,root,root) %{_datadir}/ovirt-guest-agent/hibernate

%{_datadir}/ovirt-guest-agent/ovirt-flush-caches

%attr (755,root,root) %{_initrddir}/ovirt-guest-agent


%changelog
* Mon Oct 23 2017 Tomáš Golembiovský <tgolembi@redhat.com> - 1.0.14-1
- New upstream version 1.0.14

* Tue Dec 06 2016 Vinzenz Feenstra <vfeenstr@redhat.com> - 1.0.13-1
- New upstream version 1.0.13

* Thu May 19 2016 Vinzenz Feenstra <vfeenstr@redhat.com> - 1.0.12-1
- New upstream version 1.0.12

* Fri Oct 16 2015 Vinzenz Feenstra <vfeenstr@redhat.com> - 1.0.11-2
- Adding ovirt container list feature (currently only docker)

* Mon Jul 20 2015 Vinzenz Feenstra <vfeenstr@redhat.com> - 1.0.11-1
- New upstream version 1.0.11

* Tue Feb 10 2015 Vinzenz Feenstra <vfeenstr@redhat.com> - 1.0.10-2
- Adding ovirt-osinfo script

* Tue Jul 01 2014 Vinzenz Feenstra <vfeenstr@redhat.com> - 1.0.10-1
- New upstream version 1.0.10

* Mon Jan 20 2014 Vinzenz Feenstra <vfeenstr@redhat.com> - 1.0.9-1
- Report swap usage of guests
- Updated pam conversation approach
- Python 2.4 compatability fix
- Some build fixes applied

* Thu Jul 11 2013 Vinzenz Feenstra <evilissimo@redhat.com> - 1.0.8-1
  - Update to version ovirt-guest-agent 1.0.8

* Wed Jul 10 2013 Vinzenz Feenstra <evilissimo@redhat.com> - 1.0.7-1
  - Initial ovirt-guest-agent RHEL6 package
