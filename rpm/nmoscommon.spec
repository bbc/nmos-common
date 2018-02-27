Name:           nmoscommon
Version:        0.1.0
Release:        5%{?dist}
License:        Internal License
Summary:        IP Studio Open Source Python Libraries

Source0:        nmoscommon-%{version}.tar.gz
Source1:        config.json

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-six                >= 1.10.0
BuildRequires:  python-flask              >= 0.10.2
BuildRequires:  python-requests           >= 2.2.1
BuildRequires:  python-jinja2
BuildRequires:  python-werkzeug
BuildRequires:  python-zmq
BuildRequires:  python-websocket-client   >= 0.13.0
BuildRequires:  python-dateutil

Requires:       python
Requires:       python-setuptools
Requires:       python-six                >= 1.10.0
Requires:       python-flask              >= 0.10.2
Requires:       python-requests           >= 2.2.1
Requires:       python-jinja2
Requires:       python-werkzeug
Requires:       python-zmq
Requires:       python-websocket-client   >= 0.13.0
Requires:       python-socketio-client
Requires:       python-flask-sockets
Requires:       pybonjour
Requires:       python-avahi
Requires:       pygobject2
Requires:       python-zmq
Requires:       python-pygments           >= 1.6
Requires:       python-dateutil
Requires:       python-flask-oauth
Requires:       python-netifaces

%description
IP Studio open source Python libraries from BBC R&D.

%prep
%setup

%build
%{py2_build}

%install
%{py2_install}

# Install config file
install -d -m 0755 %{buildroot}%{_sysconfdir}/nmoscommon
install -D -p -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/nmoscommon/config.json

%post
getent group ipstudio >/dev/null || groupadd -r ipstudio
getent passwd ipstudio >/dev/null || \
    useradd -r -g ipstudio -d /dev/null -s /sbin/nologin \
        -c "IP Studio user" ipstudio
mkdir -p /etc/nmoscommon
chown -R ipstudio:ipstudio /etc/nmoscommon || true

%clean
rm -rf %{buildroot}

%files
%{python2_sitelib}/nmoscommon
%{python2_sitelib}/nmoscommon-%{version}*.egg-info

%defattr(-,ipstudio,ipstudio,-)
%config(noreplace) %{_sysconfdir}/nmoscommon/config.json

%changelog
* Mon Nov 13 2017 Simon Rankine <simon.rankine@bbc.co.uk> - 0.1.0-1
- Initial packaging for RPM
