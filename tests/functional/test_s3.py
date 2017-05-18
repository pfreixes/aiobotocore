import pytest

from unittest.mock import patch, MagicMock
from yarl import URL

from aiobotocore import get_session
from aiobotocore.endpoint import ClientResponseProxy


async def build_response(content, status=200, headers=None):
    r = ClientResponseProxy("get", URL("http://example.com"))
    r._response.raw_headers = headers if headers else {}
    r._response.headers = headers if headers else {}
    r._response.status = status
    r._response._content = content
    r._response._loop = MagicMock()
    return r


class TestS3GetBucketLifecycle:

    @pytest.mark.asyncio
    async def test_multiple_transitions_returns_one(self, loop):
        content = (
            '<?xml version="1.0" ?>'
            '<LifecycleConfiguration xmlns="http://s3.amazonaws.'
            'com/doc/2006-03-01/">'
            '	<Rule>'
            '		<ID>transitionRule</ID>'
            '		<Prefix>foo</Prefix>'
            '		<Status>Enabled</Status>'
            '		<Transition>'
            '			<Days>40</Days>'
            '			<StorageClass>STANDARD_IA</StorageClass>'
            '		</Transition>'
            '		<Transition>'
            '			<Days>70</Days>'
            '			<StorageClass>GLACIER</StorageClass>'
            '		</Transition>'
            '	</Rule>'
            '	<Rule>'
            '		<ID>noncurrentVersionRule</ID>'
            '		<Prefix>bar</Prefix>'
            '		<Status>Enabled</Status>'
            '		<NoncurrentVersionTransition>'
            '			<NoncurrentDays>40</NoncurrentDays>'
            '			<StorageClass>STANDARD_IA</StorageClass>'
            '		</NoncurrentVersionTransition>'
            '		<NoncurrentVersionTransition>'
            '			<NoncurrentDays>70</NoncurrentDays>'
            '			<StorageClass>GLACIER</StorageClass>'
            '		</NoncurrentVersionTransition>'
            '	</Rule>'
            '</LifecycleConfiguration>'
        ).encode('utf-8')

        with patch("aiobotocore.endpoint.aiohttp.ClientSession.request") as\
                request:
            session = get_session(loop=loop)
            async with session.create_client('s3') as s3:
                request.return_value = build_response(content, status=200)
                response = await s3.get_bucket_lifecycle(Bucket='mybucket')

                # Each Transition member should have at least one of the
                # transitions provided.
                assert response['Rules'][0]['Transition'] ==\
                    {'Days': 40, 'StorageClass': 'STANDARD_IA'}

                assert response['Rules'][1]['NoncurrentVersionTransition'] ==\
                    {'NoncurrentDays': 40, 'StorageClass': 'STANDARD_IA'}
