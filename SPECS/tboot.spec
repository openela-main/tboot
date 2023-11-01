Summary:        Performs a verified launch using Intel TXT
Name:           tboot
Version:        1.10.5
Release:        2%{?dist}
Epoch:          1

Group:          System Environment/Base
License:        BSD
URL:            http://sourceforge.net/projects/tboot/
Source0:        http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz

BuildRequires:  openssl-devel
BuildRequires:	perl
ExclusiveArch:  %{ix86} x86_64
Requires:  	grub2-efi-x64-modules

Patch01: 0001-fix-typo-in-lcp2_crtpollist-manpage.patch
Patch02: 0002-check-for-client-server-match.patch

%description
Trusted Boot (tboot) is an open source, pre-kernel/VMM module that uses
Intel Trusted Execution Technology (Intel TXT) to perform a measured
and verified launch of an OS kernel/VMM.

%prep
%autosetup -S git

# do not override OPTFLAGS
sed -i -e 's/-march=i686//' Config.mk

%build
CFLAGS="$RPM_OPT_FLAGS"; export CFLAGS
LDFLAGS="$RPM_LD_FLAGS"; export LDFLAGS
make debug=y %{?_smp_mflags}

%post
# create the tboot entry and copy the modules to the grubenvdir
grublib='/usr/lib/grub/x86_64-efi/'

if [ -d /sys/firmware/efi ]; then
	echo "EFI detected .."
	grubenvdir='/boot/efi/EFI/redhat'
else
	echo "Legacy BIOS detected .."
	grubenvdir='/boot/grub2'
	# If previous install put the modules in the wrong dir
	[ -d /boot/efi/EFI/redhat/x86_64-efi ] && rm -rf /boot/efi/EFI/redhat/x86_64-efi
fi

grub2-mkconfig -o $grubenvdir/grub.cfg
[ -d $grubenvdir/x86_64-efi ] || mkdir -pv $grubenvdir/x86_64-efi
cp -vf $grublib/relocator.mod $grubenvdir/x86_64-efi/
cp -vf $grublib/multiboot2.mod $grubenvdir/x86_64-efi/

%postun
# Cleanup all tboot files

# Remove residual grub efi modules.
if [ -d /sys/firmware/efi ]; then
	echo "EFI detected .."
	grubenvdir='/boot/efi/EFI/redhat'
else
	echo "Legacy BIOS detected .."
	grubenvdir='/boot/grub2'
fi

[ -d $grubenvdir/x86_64-efi ] && rm -rf $grubenvdir/x86_64-efi
grub2-mkconfig -o $grubenvdir/grub.cfg

%install
echo "installing tboot"
make debug=y DISTDIR=$RPM_BUILD_ROOT install

%files
%doc README.md COPYING docs/* lcptools-v2/lcptools.txt
%config %{_sysconfdir}/grub.d/20_linux_tboot
%config %{_sysconfdir}/grub.d/20_linux_xen_tboot
%{_sbindir}/txt-acminfo
%{_sbindir}/lcp2_crtpol
%{_sbindir}/lcp2_crtpolelt
%{_sbindir}/lcp2_crtpollist
%{_sbindir}/lcp2_mlehash
%{_sbindir}/txt-parse_err
%{_sbindir}/tb_polgen
%{_sbindir}/txt-stat
%{_mandir}/man8/txt-acminfo.8.gz
%{_mandir}/man8/tb_polgen.8.gz
%{_mandir}/man8/txt-stat.8.gz
%{_mandir}/man8/lcp2_crtpol.8.gz
%{_mandir}/man8/lcp2_crtpolelt.8.gz
%{_mandir}/man8/lcp2_crtpollist.8.gz
%{_mandir}/man8/lcp2_mlehash.8.gz
%{_mandir}/man8/txt-parse_err.8.gz
/boot/tboot.gz
/boot/tboot-syms

%changelog
* Fri Aug 26 2022 Tony Camuso <tcamuso@redhat.com> - 1:1.10.5-2
- The install scriptlet in %post was not choosing the correct
  grubenv directory. In RHEL8, the efi and legacy bios grubenv
  directories are different. This change assures that the
  correct directory is used for grub.cfg and related modules.
  Added a %postun section to cleanup when removing tboot with
  dnf erase.
  Resolves: rhbz#2121836

* Wed Apr 20 2022 Tony Camuso <tcamuso@redhat.com> - 1:1.10.5-1
  Upgrade to tboot-1.10.5-1 for fixes and updates.
  Added a scriptlet to the tboot.spec file to automatically install
  grub2-efi-x64-modules and move them to the correct directory.
  Resolves: rhbz#2040082
  Resolves: rhbz#2041759

* Thu Jun 10 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.1-1
  Upgrade to tboot-1.10.2-1 provides some bug fixes and updates.
  Remove 0001-Do-not-install-man-pages-for-deprecated-tools.patch
  from the git repo, since it is no longer needed.
  Resolves: rhbz#1857068
  Resolves: rhbz#1873296
  Resolves: rhbz#1920386

* Mon Feb 22 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.0-1
  Need to add BuildRequires: perl, since it has beem moved
  from BuildRoot.
  See: https://fedoraproject.org/wiki/Packaging:Perl#Build_Dependencies
  Resolves: rhbz#1857068

* Mon Feb 22 2021 Tony Camuso <tcamuso@redhat.com> - 1:1.10.0-1
  Build problem creating directory for grub modules. We can't
  know if the modules are there, so it's up to the end user to
  find the modules and copy them to the correct location.
  Specifically, for systems booting from EFI, the
  /boot/efi/EFI/redhat/x86_64-efi/multiboot2.mod file, if it
  exists, must be copied to the /boot/efi/EFI/redhat/x86_64-efi/
  directory. If that file does not exist, then the system has
  the wrong version of grub for using tboot in an EFI system.
  Resolves: rhbz#1857068

* Fri Dec 11 2020 Tony Camuso <tcamuso@redhat.com> - 1:1.10.0-0
  Upgrade to latest upstream version
  Added upstream patch to remove deprecated man pages
  Resolves: rhbz#1857068

* Tue Jun 23 2020 Tony Camuso <tcamuso@redhat.com> - 1:1.9.12-2
- Fix build issues with one upstream patch.
  This patch also reverts the previous patch concerning the
  -Wno-address-of-packed-member cflag.
  Resolves: rhbz#1847938

* Fri Jun 12 2020 Tony Camuso <tcamuso@redhat.com> - 1:1.9.12-1
- Add patch to revert "Disable GCC9 address-of-packed-member warning"
  While it was able to build locally with 'rhpkg local', the brew
  build failed, because the compiler on the brew systems did not
  recognized the new GCC9 command line flag:
  -Wno-address-of-packed-member

* Fri May 29 2020 Tony Camuso <tcamuso@redhat.com> - 1:1.9.12-1
- Upgrade to latest upstream version
  Resolves: rhbz#1790169

* Fri Nov 15 2019 Tony Camuso <tcamuso@redhat.com> - 1:1.9.10-1
- Rebase to the lastest upstream version.
  Resolves: rhbz#1725661

* Fri Sep 7 2018 Tony Camuso <tcamuso@redhat.com> - 1:1.9.7-1
- Rebase to the latest upstream version.
  Resolves: rhbz#1511799
- Do not override OPTFLAGS in the make
  Resolves: rhbz#1620070

* Fri Jul 20 2018 Tony Camuso <tcamuso@redhat.com> - 1:1.9.6-3
- Incorporate latest upstream patches, including a newer version
  of the OpenSSL patch in 1.9.6-2
  Resolves: rhbz#1492771
  Resolves: rhbz#1499435

* Tue Feb 06 2018 Tomáš Mráz <tmraz@redhat.com> - 1:1.9.6-2
- Patch to build with OpenSSL-1.1.x

* Sun Feb 04 2018 Filipe Rosset <rosset.filipe@gmail.com> - 1:1.9.6-1
- Upgrade to latest upstream version

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Jul 30 2014 Gang Wei <gang.wei@intel.com> - 1:1.8.2-1
- Upgrade to latest upstream version which provided security fix for:
  tboot:argument measurement vulnerablity for GRUB2+ELF kernels

* Wed Jun 18 2014 Gang Wei <gang.wei@intel.com> - 1:1.8.1-1
- Upgrade to latest upstream version

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.7.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.7.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue Apr 02 2013 Gang Wei <gang.wei@intel.com> - 1:1.7.3-3
- Fix for breaking grub2-mkconfig operation in 32bit case(#929384)

* Wed Feb 20 2013 Gang Wei <gang.wei@intel.com> - 1:1.7.3-2
- Fix version string in log

* Wed Jan 30 2013 David Cantrell <dcantrell@redhat.com> - 1:1.7.3-1
- Upgrade to latest upstream version (#902653)

* Wed Aug 22 2012 Gang Wei <gang.wei@intel.com> - 1:1.7.0-2
- Fix build error with zlib 1.2.7

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.7.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sun Jan 15 2012 Gang Wei <gang.wei@intel.com> - 1:1.7.0
- 1.7.0 release

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 20110429-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Fri Apr 29 2011 Gang Wei <gang.wei@intel.com> - 20110429-1
- Pull upstream changeset 255, rebuilt in F15

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 20101005-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Dec 1 2010 Joseph Cihula <joseph.cihula@intel.com> - 20101005-1.fc13
- Initial import
