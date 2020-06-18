%global srcname newdoc

Name:           python-%{srcname}
Version:        1.4.3
Release:        2%{?dist}
Summary:        A script to generate assembly and module AsciiDoc files from templates

License:        GPLv3+
URL:            https://pypi.python.org/pypi/%{srcname}
Source0:        %pypi_source

BuildArch:      noarch
BuildRequires:  python2-devel python3-devel

%description
A script to generate assembly and module AsciiDoc files from templates

%package -n python2-%{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{srcname}}

%description -n python2-%{srcname}
A script to generate assembly and module AsciiDoc files from templates


%package -n python3-%{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
A script to generate assembly and module AsciiDoc files from templates


%prep
%autosetup -n %{srcname}-%{version}

%build
%py2_build
%py3_build

%install
# Must do the python2 install first because the scripts in /usr/bin are
# overwritten with every setup.py install, and in general we want the
# python3 version to be the default.
# If, however, we're installing separate executables for python2 and python3,
# the order needs to be reversed so the unversioned executable is the python2 one.
%py2_install
%py3_install

%check
%{__python2} setup.py test
%{__python3} setup.py test

# Note that there is no %%files section for the unversioned python module if we are building for several python runtimes
%files -n python2-%{srcname}
%license LICENSE
%doc README.rst
%{python2_sitelib}/*

%files -n python3-%{srcname}
%license LICENSE
%doc README.rst
%{python3_sitelib}/*
%{_bindir}/newdoc

%changelog
* Mon Oct 07 2019 Marek Suchánek <msuchane@redhat.com> 1.4.3-1
- Fix a reference to the renamed readme in the RPM spec (msuchane@redhat.com)
- Updated the changelog (msuchane@redhat.com)

* Mon Sep 30 2019 Marek Suchánek <msuchane@redhat.com> 1.4.2-1
- Fix: Remove a redundant, outdated statement to restore assembly context
  (msuchane@redhat.com)

* Sat Aug 31 2019 Marek Suchánek <msuchane@redhat.com> 1.4.1-1
- Converted the readme to RST because PyPI literally can't handle anything else
  (msuchane@redhat.com)

* Thu Aug 29 2019 Marek Suchánek <msuchane@redhat.com> 1.4.0-1
- Updated the templates to match upstream; Issue#18
  (msuchane@redhat.com)
- Added a readme on building and releasing new package versions
  (msuchane@redhat.com)
- Improved ID substitutions (msuchane@redhat.com)

* Thu Aug 29 2019 Marek Suchánek <msuchane@redhat.com> 1.3.3-1
- Fix the version once more (learning tito, sorry)

* Thu Aug 29 2019 Marek Suchánek <msuchane@redhat.com> v1.3.2-1
- Bump the version for building purposes

* Wed Aug 28 2019 Marek Suchánek <msuchane@redhat.com> v1.3.1-1
- Enable the tito packaging system

