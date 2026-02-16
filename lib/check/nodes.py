from libprobe.asset import Asset
from libprobe.check import Check
from ..connector import get_conn


class CheckNodes(Check):
    key = 'nodes'
    unchanged_eol = 0

    @staticmethod
    async def run(asset: Asset, local_config: dict, config: dict) -> dict:
        conn, lock = await get_conn(local_config, asset.name)
        async with lock:
            node_ids = await conn.query("""//ti
                nodes_info().map(|n| n.load().node_id);
            """, scope='/node')

            nodes = []

            for node_id in node_ids:
                node_info, counters, backups_ok = await conn.query("""//ti
                    [node_info(), counters(), backups_ok()];
                """, scope=f'/node/{node_id}')
                node_info.update(counters)
                node_info['backups_ok'] = backups_ok
                nodes.append(node_info)

        items = [{
            'name': str(node['node_id']),
            'backups_ok': node['backups_ok'],
            'changes_in_queue': node['changes_in_queue'],
            'connected_clients': node['connected_clients'],
            'global_committed_change_id': node['global_committed_change_id'],
            'local_committed_change_id': node['local_committed_change_id'],
            'log_level': node['log_level'],
            'node_name': node['node_name'],
            'uptime': int(node['uptime']),
            'version': node['version'],
            'counters_average_query_duration': node['average_query_duration'],
            'counters_changes_failed': node['changes_failed'],
            'counters_changes_killed': node['changes_killed'],
            'counters_changes_skipped': node['changes_skipped'],
            'counters_changes_unaligned': node['changes_unaligned'],
            'counters_changes_with_gap': node['changes_with_gap'],
            'counters_garbage_collected': node['garbage_collected'],
            'counters_largest_result_size': node['largest_result_size'],
            'counters_quorum_lost': node['quorum_lost'],
            'counters_started_at': node['started_at'],
        } for node in nodes]

        state = {'nodes': items}
        return state
