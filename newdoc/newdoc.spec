%global srcname newdoc

Name:           python-%{srcname}
Version:        v1.3.2
Release:        1%{?dist}
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
%doc README.md
%{python2_sitelib}/*

%files -n python3-%{srcname}
%license LICENSE
%doc README.md
%{python3_sitelib}/*
%{_bindir}/newdoc

%changelog
* Thu Aug 29 2019 Marek Suchánek <msuchane@redhat.com> v1.3.2-1
- Bump the version for building purposes

* Wed Aug 28 2019 Marek Suchánek <msuchane@redhat.com> v1.3.1-1
- Enable the tito packaging system

