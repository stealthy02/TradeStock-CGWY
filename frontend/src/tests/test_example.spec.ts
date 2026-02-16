// 前端测试示例文件
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HelloWorld from '@/components/HelloWorld.vue'

describe('HelloWorld.vue', () => {
  it('renders props.msg when passed', () => {
    const msg = 'new message'
    const wrapper = mount(HelloWorld, {
      props: { msg }
    })
    expect(wrapper.text()).toContain(msg)
  })

  it('renders default message when no msg prop', () => {
    const wrapper = mount(HelloWorld)
    expect(wrapper.text()).toContain('Hello World')
  })
})
