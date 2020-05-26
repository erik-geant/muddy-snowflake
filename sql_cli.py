import json
import sys

import click
import jsonschema
import pymysql

from dashboard_v3_checks import stats

CONFIG_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'type': 'object',
    'properties': {
        'hostname': {'type': 'string'},
        'username': {'type': 'string'},
        'password': {'type': 'string'},
    },
    'required': ['hostname', 'username', 'password'],
    'additionalProperties': False
}


def validate_config(ctx, param, value):
    """
    loads, validates and returns configuration parameters

    :param ctx:
    :param param:
    :param value: filename (string)
    :return: a dict containing configuration parameters
    """
    try:
        with open(value) as f:
            config = json.loads(f.read())
        jsonschema.validate(config, CONFIG_SCHEMA)
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        raise click.BadParameter(str(e))

    return config


def _get_status_field_rows(hostname, username, password):
    """
    this method contains all sql i/o so we can mock it for testing
    :param hostname:
    :param username:
    :param password:
    :return:
    """
    # Open database connection
    db = pymysql.connect(host=hostname, user=username, password=password)

    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    cursor.execute("SHOW GLOBAL STATUS LIKE 'wsrep_%'")
    for r in cursor.fetchall():
        yield r

    cursor.execute("SHOW GLOBAL STATUS LIKE 'com_%'")
    for r in cursor.fetchall():
        yield r

    # disconnect from server
    db.close()


def get_status_fields(hostname, username, password):
    status = {}
    try:
        for r in _get_status_field_rows(hostname, username, password):
            status[r[0]] = r[1]
    except pymysql.MySQLError as e:
        print(e)
        sys.exit(stats.SENSU_EXIT_CRITICAL)

    return status


def get_influx_line(measurement, tags, status):
    counters_to_capture = {
        'commit': 'Com_commit',
        'insert': 'Com_insert',
        'rollback': 'Com_rollback',
        'select': 'Com_select',
        'update': 'Com_update',
        'delete': 'Com_delete',
        'cluster_size': 'wsrep_cluster_size'
    }

    try:
        fields = dict([
            (k, int(status[v])) for k, v in counters_to_capture.items()
        ])
    except KeyError as e:
        print('expected state key not found: %s' % e)
        sys.exit(stats.SENSU_EXIT_CRITICAL)

    def _key_values(d):
        return ['%s=%s' % (k, v) for k, v in d.items()]

    return '{measurement},{tags} {fields}'.format(
        measurement=measurement,
        tags=','.join(_key_values(tags)),
        fields=','.join(_key_values(fields)))


def verify_bigger_than_two(ctx, param, value):
    """
    ok if value is None, otherwise verify >= 2

    :param ctx:
    :param param:
    :param value: integer value
    :return: the value or None
    """
    if value is None:
        return None

    if value < 2:
        raise click.BadParameter('value must be at least 2')

    return value


@click.command()
@click.option(
    '--config',
    required=True,
    type=click.STRING,
    callback=validate_config,
    help='configuration filename')
@click.option(
    '--cluster-size',
    required=False,
    default=None,
    type=click.INT,
    callback=verify_bigger_than_two,
    help='expected cluster size')
@click.option(
    '--measurement',
    required=True,
    type=click.STRING,
    help='influx measurement name')
def main(config, measurement, cluster_size):
    status = get_status_fields(
        hostname=config['hostname'],
        username=config['username'],
        password=config['password'])

    message = get_influx_line(
        measurement=measurement,
        tags={'hostname': config['hostname']},
        status=status)
    print(message)

    exit_code = stats.SENSU_EXIT_OK

    if cluster_size and \
            int(status['wsrep_cluster_size']) != cluster_size:
        print('degraded cluster: wsrep_cluster_size == %s (expected %d)'
              % (status['wsrep_cluster_size'], cluster_size))
        exit_code = stats.SENSU_EXIT_WARNING

    critical_checks = {
        'wsrep_connected': 'ON',
        'wsrep_ready': 'ON',
        'wsrep_local_state_comment': 'Synced',
    }

    for key, expected in critical_checks.items():
        value = status.get(key, None)
        if value != expected:
            print(
                "ERROR: %s = '%s' (expected '%s')" % (key, value, expected))
            exit_code = stats.SENSU_EXIT_CRITICAL

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
