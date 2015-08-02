ROLLNAME	= os-$(shell rocks report version)-security-updates
NAME		= os-$(shell rocks report version)-security-updates
RELEASE		= 0
COLOR		= royalblue
ISOSIZE		= 0
VERSION		= $(shell date +%F | tr - _)

REDHAT.ROOT	= $(PWD)
REPOSDIR 	= yum.repos.d
CACHEDIR	= var/cache/yum
LOGDIR		= var/log
