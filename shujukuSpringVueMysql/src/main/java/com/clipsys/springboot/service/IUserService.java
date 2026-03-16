package com.clipsys.springboot.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.clipsys.springboot.entity.User;
import com.clipsys.springboot.controller.dto.UserDTO;
import com.clipsys.springboot.controller.dto.UserPasswordDTO;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * <p>
 *  服务类
 * </p>
 */
public interface IUserService extends IService<User> {

    UserDTO login(UserDTO userDTO);

    User register(UserDTO userDTO);

    void updatePassword(UserPasswordDTO userPasswordDTO);

    Page<User> findPage(Page<User> objectPage, String username, String email, String address);
}
