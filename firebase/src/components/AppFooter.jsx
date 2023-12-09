import React from 'react';
import { Layout } from 'antd';

const { Footer } = Layout;

const AppFooter = () => {
    return(
        <Footer style={{ textAlign: 'center' }}>
            <p>Created by <a href={'https://www.ukclimbing.com/user/profile.php?id=256853'}>Tom Moses</a></p>
            <img src='/api_logo_pwrdBy_strava_horiz_gray.png' height={32} />
        </Footer>
    )
}

export default AppFooter;