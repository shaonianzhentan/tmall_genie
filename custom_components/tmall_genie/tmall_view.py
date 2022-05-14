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
        if options.get('debug', False) == True:
            await hass.services.async_call('persistent_notification', 'create', {
                'title': '接收信息',
                'message': json.dumps(data, indent=2)
            })

        header = data['header']
        payload = data['payload']
        name = header['name']
        accessToken = payload['accessToken']
        # 验证权限
        token = await hass.auth.async_validate_access_token(accessToken)
        # 进行自定义服务验证
        if token is None:
            voice = hass.data["conversation_voice"]
            config_data = voice.api_config.get_config()
            apiKey = config_data.get('apiKey', '')
            # 判断是否定义apiKey
            if apiKey != '' and accessToken == f'apiKey{apiKey}':
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
        
        if options.get('debug', False) == True:
            await hass.services.async_call('persistent_notification', 'create', {
                'title': '发送信息',
                'message': json.dumps(response, indent=2)
            })
        return self.json(response)