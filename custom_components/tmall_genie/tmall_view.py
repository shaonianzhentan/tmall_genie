import logging, json
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN, TMALL_API
from .tmall import discoveryDevice, controlDevice, errorResult

class TmallView(HomeAssistantView):

    url = TMALL_API
    name = TMALL_API[1:].replace('/', ':')
    requires_auth = False

    async def post(self, request):
        hass = request.app["hass"]
        data = await request.json()
        
        options = hass.data[DOMAIN]
        apiKey = options.get('apiKey')
        is_debug = options.get('debug', False)
        if is_debug:
            await hass.services.async_call('persistent_notification', 'create', {
                'title': '接收信息',
                'message': json.dumps(data, indent=2)
            })

        header = data['header']
        payload = data['payload']
        name = header['name']
        accessToken = payload['accessToken']

        token = None
        # 授权验证
        if accessToken == f'apiKey{apiKey}':
            token = accessToken

        # 走正常流程
        result = {}
        if token is not None:
            namespace = header['namespace']
            if namespace == 'AliGenie.Iot.Device.Discovery':
                # 发现设备
                result = await discoveryDevice(hass)
                name = 'DiscoveryDevicesResponse'
            elif namespace == 'AliGenie.Iot.Device.Control':
                # 控制设备
                result = await controlDevice(hass, name, payload)
                name = 'CorrectResponse'
        else:
            result = errorResult('ACCESS_TOKEN_INVALIDATE')

        # Check error and fill response name
        header['name'] = name        
        response = {'header': header, 'payload': result}
        
        if is_debug:
            await hass.services.async_call('persistent_notification', 'create', {
                'title': '发送信息',
                'message': json.dumps(response, indent=2)
            })
        return self.json(response)