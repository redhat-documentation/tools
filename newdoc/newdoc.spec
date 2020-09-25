%global srcname newdoc

Name:           python-%{srcname}
Version:        1.5.1
Release:        1
Summary:        A script to generate assembly and module AsciiDoc files from templates

License:        GPLv3+
URL:            https://pypi.python.org/pypi/%{srcname}
Source0:        %pypi_source

BuildArch:      noarch
BuildRequires:  python3-devel

%description
A script to generate assembly and module AsciiDoc files from templates

%package -n python3-%{srcname}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
A script to generate assembly and module AsciiDoc files from templates


%prep
%autosetup -n %{srcname}-%{version}

%build
%py3_build

%install
%py3_install

%check
%{__python3} setup.py test

%files -n python3-%{srcname}
%license LICENSE
%doc README.rst
%{python3_sitelib}/*
%{_bindir}/newdoc

%changelog
* Fri Sep 25 2020 Marek Suchánek <msuchane@redhat.com> 1.5.1-1
- Announce the deprecation of this version and the migration to the new one
  (msuchane@redhat.com)

* Tue Jun 23 2020 Marek Suchánek <msuchane@redhat.com> 1.5.0-1
- Remove the remaining Python 2 code (msuchane@redhat.com)
- Align the Optional formatting with the IBM Style Guide; #29
  (msuchane@redhat.com)
- Remove Python 2 packaging (marek.suchanek@protonmail.com)
- Update outdated version information (marek.suchanek@protonmail.com)
- Clarify newdoc install instructions (msuchane@redhat.com)

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

