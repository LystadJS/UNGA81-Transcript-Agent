"""Bounded metadata-only storage accounting, including reachable Git history.

Provider usage is not assumed to count ordinary Git blobs. Logical object sizes
are not exact packed disk usage or an account-wide quota certification.
"""
from datetime import datetime, timezone
import re
from .snapshots import _provider_call


class CapacityIncomplete(ValueError):
    pass


def count(value):
    if type(value) is not int or value<0:raise CapacityIncomplete('Invalid storage metadata size')
    return value


def oid(value, width=40):
    if not isinstance(value,str) or not re.fullmatch('[a-fA-F0-9]{'+str(width)+'}',value):
        raise CapacityIncomplete('Unpinned storage metadata identity')
    return value.lower()


def references(storage, max_refs):
    refs=_provider_call('capacity_refs',storage.api.list_repo_refs,storage.repo_id,repo_type='dataset',include_pull_requests=True)
    result=[]
    for group in ('branches','tags','converts','pull_requests'):
        entries=getattr(refs,group,None)
        if not isinstance(entries,list):raise CapacityIncomplete('Complete repository refs unavailable')
        for item in entries:
            name=getattr(item,'ref',None)
            if not isinstance(name,str) or not name:raise CapacityIncomplete('Invalid repository ref metadata')
            result.append((name,oid(item.target_commit)))
            if len(result)>max_refs:raise CapacityIncomplete('Repository ref accounting bound exceeded')
    if len({name for name,_ in result})!=len(result):raise CapacityIncomplete('Duplicate repository refs')
    return sorted(result)


def tree_entries(storage, revision):
    # The SDK paginates lazily: HTTP failures may happen during next(), after
    # an initial successful response. Sanitize both boundaries identically.
    entries=iter(_provider_call('capacity_tree',storage.api.list_repo_tree,storage.repo_id,
                               repo_type='dataset',revision=revision,recursive=True,expand=False))
    while True:
        try:entry=_provider_call('capacity_tree',next,entries)
        except StopIteration:return
        yield entry


def measure_capacity(storage, *, max_refs=16, max_commits=200, max_entries=500000):
    info,provider_bytes=storage.info();head=oid(info.sha)
    initial_refs=references(storage,max_refs)
    tips={head}|{revision for _,revision in initial_refs}
    commits=set()
    for tip in sorted(tips):
        history=_provider_call('capacity_commits',storage.api.list_repo_commits,storage.repo_id,repo_type='dataset',revision=tip)
        if not history or len(history)>max_commits:raise CapacityIncomplete('Commit accounting bound exceeded or history absent')
        ids={oid(item.commit_id) for item in history}
        if len(ids)!=len(history) or tip not in ids:raise CapacityIncomplete('Incomplete commit identity inventory')
        commits.update(ids)
        if len(commits)>max_commits:raise CapacityIncomplete('Commit accounting bound exceeded')
    git_blobs={};large_blobs={};visits=0;current_files=current_bytes=current_git_files=current_large_files=0
    def remember(target,identity,size):
        if identity in target and target[identity]!=size:raise CapacityIncomplete('Object size changes across immutable identities')
        target[identity]=size
    for revision in sorted(commits):
        paths=set()
        for entry in tree_entries(storage,revision):
            visits+=1
            if visits>max_entries:raise CapacityIncomplete('Tree metadata accounting bound exceeded')
            path=getattr(entry,'path',None)
            if not isinstance(path,str) or path in paths:raise CapacityIncomplete('Invalid or repeated tree metadata path')
            paths.add(path)
            blob=getattr(entry,'blob_id',None)
            if blob is None:
                oid(getattr(entry,'tree_id',None));continue
            blob=oid(blob);size=count(entry.size);large=getattr(entry,'lfs',None)
            if large is None:
                remember(git_blobs,blob,size)
            else:
                if count(large.size)!=size:raise CapacityIncomplete('Inconsistent large-file metadata')
                remember(git_blobs,blob,count(large.pointer_size))
                remember(large_blobs,oid(large.sha256,64),size)
            if revision==head:
                current_files+=1;current_bytes+=size
                current_git_files+=int(large is None);current_large_files+=int(large is not None)
    final,final_provider_bytes=storage.info()
    if oid(final.sha)!=head or references(storage,max_refs)!=initial_refs:
        raise CapacityIncomplete('Repository changed during capacity measurement')
    provider_bytes=max(count(provider_bytes),count(final_provider_bytes))
    git_bytes=sum(git_blobs.values());large_bytes=sum(large_blobs.values())
    return {'schema':'un.storage-capacity.v1','measured_at':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
            'role':'private' if storage.private else 'public','revision':head,
            'provider_reported_bytes':provider_bytes,'current_tree_files':current_files,
            'current_tree_logical_bytes':current_bytes,'current_tree_regular_files':current_git_files,
            'current_tree_large_files':current_large_files,'reachable_refs':len(initial_refs),
            'reachable_commits':len(commits),'metadata_entries_examined':visits,
            'reachable_unique_git_objects':len(git_blobs),'reachable_unique_git_blob_bytes':git_bytes,
            'reachable_unique_large_objects':len(large_blobs),'reachable_unique_large_bytes':large_bytes,
            'budget_basis_bytes':max(provider_bytes,large_bytes)+git_bytes,
            'budget_basis':'max(provider_reported_bytes, reachable_unique_large_bytes) + reachable_unique_git_blob_bytes',
            'configured_budget_bytes':storage.budget_bytes,'history_inventory_complete_for_returned_refs':True,
            'account_capacity_accepted':False,'physical_storage_exact':False,
            'source_contents_read':False,
            'limitations':['Logical object sizes exclude Git commit/tree overhead and packing effects.',
                           'Provider-meter semantics, unadvertised/unreachable objects and other account repositories remain outside this inventory.']}
